from panda3d.bsp import NetworkSystem, NetworkCallbacks, NetworkConnectionInfo, NetworkMessage
from panda3d.core import UniqueIdAllocator, HashVal
from panda3d.direct import FrameSnapshot, ClientFrameManager, ClientFrame, FrameSnapshotManager, DCPacker

from direct.distributed.PyDatagram import PyDatagram
from direct.showbase.DirectObject import DirectObject
from direct.directnotify.DirectNotifyGlobal import directNotify

from .NetMessages import NetMessages
from .ServerConfig import *
from .BaseObjectManager import BaseObjectManager

from enum import IntEnum

class ClientState(IntEnum):

    Unverified = 0
    Verified = 1

class ServerRepository(BaseObjectManager):

    notify = directNotify.newCategory("ServerRepository")
    notify.setDebug(False)

    class Client:

        def __init__(self, connection, netAddress, id = -1):
            self.id = id
            self.connection = connection
            self.netAddress = netAddress
            self.state = ClientState.Unverified
            # How many times per second this client should receive
            # state snapshots.
            self.updateRate = 0
            self.updateInterval = 0
            self.nextUpdateTime = 0.0
            # How many times per second this client sends us
            # commands.
            self.cmdRate = 0
            self.cmdInterval = 0

            # What tick are they currently on?
            self.prevTickCount = 0
            self.dt = 0
            self.tickRemainder = 0
            self.tickCount = 0

            self.frameMgr = ClientFrameManager()

            # Last sent snapshot
            self.lastSnapshot = None

            # Current client frame
            self.currentFrame = None

            self.objectsByDoId = {}
            self.objectsByZoneId = {}
            self.explicitInterestZoneIds = set()
            self.currentInterestZoneIds = set()

        def getClientFrame(self, tick):
            return self.frameMgr.getClientFrame(tick)

        def setupPackInfo(self, snapshot):
            frame = ClientFrame(snapshot)
            maxFrames = 128
            if maxFrames < self.frameMgr.addClientFrame(frame):
                self.frameMgr.removeOldestFrame()
            self.currentFrame = frame

        def isVerified(self):
            return self.state == ClientState.Verified and self.id != -1

    def __init__(self, listenPort):
        BaseObjectManager.__init__(self, False)
        self.dcSuffix = 'AI'

        # The client that just sent us a message.
        self.clientSender = None

        self.listenPort = listenPort
        self.netSys = NetworkSystem()
        self.netCallbacks = NetworkCallbacks()
        self.netCallbacks.setCallback(self.__handleNetCallback)
        self.listenSocket = self.netSys.createListenSocket(listenPort)
        self.pollGroup = self.netSys.createPollGroup()
        self.clientIdAllocator = UniqueIdAllocator(0, 0xFFFF)
        self.objectIdAllocator = UniqueIdAllocator(0, 0xFFFF)
        self.numClients = 0
        self.clientsByConnection = {}
        self.zonesToClients = {}

        self.snapshotMgr = FrameSnapshotManager()

        self.objectsByZoneId = {}

        base.setTickRate(sv_tickrate.getValue())
        base.simTaskMgr.add(self.runFrame, "serverRunFrame", sort = -100)

    def allocateObjectID(self):
        return self.objectIdAllocator.allocate()

    def freeObjectID(self, id):
        self.objectIdAllocator.free(id)

    # Generate a distributed object on the network
    # Can be given a client owner, in which that client will generate an
    # owner-view instance of the object.
    def generateObject(self, do, zoneId, owner = None):
        do.zoneId = zoneId
        do.doId = self.allocateObjectID()
        do.dclass = self.dclassesByName[do.__class__.__name__]
        do.owner = owner
        self.doId2do[do.doId] = do
        self.objectsByZoneId.setdefault(do.zoneId, []).append(do)
        if owner:
            owner.objectsByDoId[do.doId] = do
            owner.objectsByZoneId.setdefault(do.zoneId, set()).add(do)

        do.generate()

        clients = set(self.zonesToClients.get(do.zoneId, set()))
        if len(clients) > 0:
            if owner:
                # Don't include the owner in this message, we send specific
                # generate for the owner.
                clients -= set(owner)
            dg = PyDatagram()
            dg.addUint16(NetMessages.SV_GenerateObject)
            self.packObjectGenerate(dg, do)
            # Inform clients interested in the object's zone
            for client in clients:
                self.sendDatagram(dg, client.connection)

        if owner:
            # Send a specific owner generate
            dg = PyDatagram()
            dg.addUint16(NetMessages.SV_GenerateOwnerObject)
            self.packObjectGenerate(dg, do)
            self.sendDatagram(dg, owner.connection)

            # Follow interest system. Client implicitly has interest in the
            # location of owned objects.
            self.updateClientInterestZones(owner)

        do.announceGenerate()

    def deleteObject(self, do, removeFromOwnerTable = True):
        del self.doId2do[do.doId]
        self.objectsByZoneId[do.zoneId].remove(do)
        if not self.objectsByZoneId[do.zoneId]:
            del self.objectsByZoneId[do.zoneId]

        if removeFromOwnerTable and (do.owner is not None):
            client = do.owner
            client.objectsByZoneId[do.zoneId].remove(do)
            if not client.objectsByZoneId[do.zoneId]:
                del client.objectsByZoneId[do.zoneId]
            del client.objectsByDoId[do.doId]

        clients = self.zonesToClients.get(do.zoneId, set())
        if len(clients) > 0:
            # Inform any clients that see the object
            dg = PyDatagram()
            dg.addUint16(NetMessages.SV_DeleteObject)
            dg.addUint32(do.doId)
            for client in clients:
                self.sendDatagram(dg, client.connection)

        # Forget this object in the packet history
        self.snapshotMgr.removePrevSentPacket(do.doId)

        do.delete()

    def simObjects(self):
        for do in self.doId2do.values():
            do.update()

    def runFrame(self, task):
        self.readerPollUntilEmpty()
        self.runCallbacks()

        self.simObjects()

        self.takeTickSnapshot(base.tickCount)

        return task.cont

    def clientNeedsUpdate(self, client):
        return client.isVerified() and client.nextUpdateTime <= globalClock.getFrameTime()

    ###########################################################
    #
    # Snapshot/object packing code
    #
    ###########################################################

    def takeTickSnapshot(self, tickCount):
        self.notify.debug("Take tick snapshot at tick %i" % tickCount)
        snap = FrameSnapshot(tickCount, len(self.doId2do))

        # Build a set of all unique client interest zones (for clients that needs snapshots)
        clientsNeedingSnapshots = []
        clientZones = set()
        for _, client in self.clientsByConnection.items():
            if self.clientNeedsUpdate(client):
                # Factor in this client's interest zones
                clientZones |= client.currentInterestZoneIds
                # Calculate when the next update should be
                client.nextUpdateTime = globalClock.getFrameTime() + client.updateInterval
                client.setupPackInfo(snap)
                clientsNeedingSnapshots.append(client)

        if len(clientsNeedingSnapshots) == 0:
            # No clients need snapshots, punt
            self.notify.debug("Punting, no clients need snapshot")
            return

        self.notify.debug("All unique client interest zones: %s" % repr(clientZones))

        # Pack all objects visible by at least one client into the snapshot.
        items = list(self.doId2do.items())
        for i in range(len(items)):
            doId, do = items[i]

            if do.zoneId not in clientZones:
                # Object not seen by any clients, omit from snapshot
                continue

            self.snapshotMgr.packObjectInSnapshot(snap, i, do, doId, do.zoneId, do.dclass)

        # Send it out to whoever needs it
        for client in clientsNeedingSnapshots:
            # Get the frame the client most recently acknowledged
            oldFrame = client.getClientFrame(client.tickCount)

            client.lastSnapshot = snap

            dg = PyDatagram()
            dg.addUint16(NetMessages.SV_Tick)
            if oldFrame:
                # We have an old frame to delta against
                self.snapshotMgr.clientFormatDeltaSnapshot(dg, oldFrame.getSnapshot(), snap, list(client.currentInterestZoneIds))
            else:
                self.snapshotMgr.clientFormatSnapshot(dg, snap, list(client.currentInterestZoneIds))
            self.sendDatagram(dg, client.connection)

    def isFull(self):
        return self.numClients >= sv_max_clients.getValue()

    def canAcceptConnection(self):
        return True

    def runCallbacks(self):
        self.netSys.runCallbacks(self.netCallbacks)

    def readerPollUntilEmpty(self):
        while self.readerPollOnce():
            pass

    def readerPollOnce(self):
        msg = NetworkMessage()
        if self.netSys.receiveMessageOnPollGroup(self.pollGroup, msg):
            self.handleDatagram(msg)
            return True
        return False

    def handleDatagram(self, msg):
        datagram = msg.getDatagram()
        connection = msg.getConnection()
        dgi = msg.getDatagramIterator()
        client = self.clientsByConnection.get(connection)

        if not client:
            self.notify.warning("SECURITY: received message from unknown source %i" % connection)
            return

        self.clientSender = client

        type = dgi.getUint16()

        if client.state == ClientState.Unverified:
            if type == NetMessages.CL_Hello:
                self.handleClientHello(client, dgi)

        elif client.state == ClientState.Verified:
            if type == NetMessages.CL_SetCMDRate:
                self.handleClientSetCMDRate(client, dgi)
            elif type == NetMessages.CL_SetUpdateRate:
                self.handleClientSetUpdateRate(client, dgi)
            elif type == NetMessages.CL_Disconnect:
                self.handleClientDisconnect(client)
            elif type == NetMessages.CL_Tick:
                self.handleClientTick(client, dgi)
            elif type == NetMessages.CL_AddInterest:
                self.handleClientAddInterest(client, dgi)
            elif type == NetMessages.CL_RemoveInterest:
                self.handleClientRemoveInterest(client, dgi)
            elif type == NetMessages.CL_SetInterest:
                self.handleClientSetInterest(client, dgi)
            elif type == NetMessages.B_ObjectMessage:
                self.handleObjectMessage(client, dgi)

    def sendUpdate(self, do, name, args, client = None):
        if not do:
            return
        if not do.dclass:
            return

        field = do.dclass.getFieldByName(name)
        if not field:
            self.notify.warning("Tried to send unknown field %s" % name)
            return
        if field.asParameter():
            self.notify.warning("Can't sent parameter field as a message")
            return

        packer = DCPacker()
        packer.rawPackUint16(NetMessages.B_ObjectMessage)
        packer.rawPackUint32(do.doId)
        packer.rawPackUint16(field.getNumber())

        packer.beginPack(field)
        field.packArgs(packer, args)
        if not packer.endPack():
            self.notify.warning("Failed to pack message")
            return

        dg = PyDatagram(packer.getBytes())
        if not client:
            if field.isBroadcast():
                # Send to all interested clients
                for cl in self.zonesToClients.get(do.zoneId, set()):
                    self.sendDatagram(dg, cl.connection)
            else:
                self.notify.warning("Can't send non-broadcast object message without a target client")
                return
        else:
            self.sendDatagram(dg, client.connection)

    def handleObjectMessage(self, client, dgi):
        doId = dgi.getUint32()
        do = self.doId2do.get(doId)
        if not do:
            self.notify.warning("SUSPICIOUS: client %i tried to send message to unknown doId %i" %
                                (client.id, doId))
            return

        fieldNumber = dgi.getUint16()
        field = do.dclass.getFieldByIndex(fieldNumber)
        if field.asParameter():
            self.notify.warning("SUSPICIOUS: client %i tried to send message on a parameter field!")
            return

        if not field:
            self.notify.warning("SUSPICIOUS: client %i tried to send message on unknown field %i on doId %i" %
                                (client.id, doId, fieldNumber))
            return

        if do.owner != client:
            if not field.isClsend():
                # Not client-send
                self.notify.warning("SUSPICIOUS: client %i tried to send non-clsend message on doId %i" %
                                    (client.id, doId))
                return
        else:
            if not field.isOwnsend() and not field.isClsend():
                # Not client-send or owner-send
                self.notify.warning("SUSPICIOUS: owner client %i tried to send non-ownsend and non-clsend message on doId %i" %
                                    (client.id, doId))
                return

        # We can safely pass this message onto the object
        packer = DCPacker()
        packer.setUnpackData(dgi.getRemainingBytes())
        packer.beginUnpack(field)
        field.receiveUpdate(packer, do)
        if not packer.endUnpack():
            self.notify.warning("Failed to unpack object message")

    def handleClientAddInterest(self, client, dgi):
        """ Called when client wants to add interest into a set of zones """
        handle = dgi.getUint8()
        numZones = dgi.getUint8()
        for _ in range(numZones):
            zoneId = dgi.getUint32()
            client.explicitInterestZoneIds.add(zoneId)

        self.updateClientInterestZones(client)
        self.sendInterestComplete(client, handle)

    def handleClientRemoveInterest(self, client, dgi):
        """ Called when client wants to remove interest from a set of zones """

        handle = dgi.getUint8()
        numZones = dgi.getUint8()
        for _ in range(numZones):
            zoneId = dgi.getUint32()

            if zoneId in client.explicitInterestZoneIds:
                client.explicitInterestZoneIds.remove(zoneId)

        self.updateClientInterestZones(client)
        self.sendInterestComplete(client, handle)

    def handleClientSetInterest(self, client, dgi):
        """ Called when client wants to completely replace its interest zones """

        client.explicitInterestZoneIds = set()

        handle = dgi.getUint8()
        numZones = dgi.getUint8()
        for _ in range(numZones):
            zoneId = dgi.getUint32()
            client.explicitInterestZoneIds.add(zoneId)

        self.updateClientInterestZones(client)
        self.sendInterestComplete(client, handle)

    def packObjectGenerate(self, dg, object):
        dg.addUint16(object.dclass.getNumber())
        dg.addUint32(object.doId)
        dg.addUint32(object.zoneId)

        # Find or create a baseline state.
        baseline = self.snapshotMgr.findOrCreateObjectPacketForBaseline(
            object, object.dclass, object.doId)
        if baseline:
            # We got a baseline, pack it into the datagram
            dg.addUint8(1)
            baseline.packDatagram(dg)
        else:
            dg.addUint8(0)

    def updateClientInterestZones(self, client):
        origZoneIds = client.currentInterestZoneIds
        newZoneIds = client.explicitInterestZoneIds | set(client.objectsByZoneId.keys())
        if origZoneIds == newZoneIds:
            # No change.
            return

        client.currentInterestZoneIds = newZoneIds
        addedZoneIds = newZoneIds - origZoneIds
        removedZoneIds = origZoneIds - newZoneIds

        dg = PyDatagram()
        dg.addUint16(NetMessages.SV_GenerateObject)
        for zoneId in addedZoneIds:
            self.zonesToClients.setdefault(zoneId, set()).add(client)

            # The client is opening interest in this zone. Need to inform
            # client of all objects in this zone.
            for object in self.objectsByZoneId.get(zoneId, []):
                if object.owner != client:
                    # Don't do this if the client owns the object, it should
                    # already be generated for them.
                    self.packObjectGenerate(dg, object)

        self.sendDatagram(dg, client.connection)

        dg = PyDatagram()
        dg.addUint16(NetMessages.SV_DeleteObject)
        for zoneId in removedZoneIds:
            self.zonesToClients[zoneId].remove(client)
            # The client is abandoning interest in this zone. Any
            # objects in this zone should be deleted on the client.
            for object in self.objectsByZoneId.get(zoneId, []):
                if object.owner != client:
                    # Never delete objects owned by this client on interest change.
                    dg.addUint32(object.doId)
        self.sendDatagram(dg, client.connection)

    def sendInterestComplete(self, client, handle):
        dg = PyDatagram()
        dg.addUint16(NetMessages.SV_InterestComplete)
        dg.addUint8(handle)
        self.sendDatagram(dg, client.connection)

    def sendDatagram(self, dg, connection):
        self.netSys.sendDatagram(connection, dg, NetworkSystem.NSFReliableNoNagle)

    def closeClientConnection(self, client):
        if client.id != -1:
            self.clientIdAllocator.free(client.id)
        self.netSys.closeConnection(client.connection)
        del self.clientsByConnection[client.connection]

    def handleClientTick(self, client, dgi):
        client.prevTickCount = int(client.tickCount)
        client.tickCount = dgi.getUint32()
        self.notify.debug("Client acknowleged tick %i" % client.tickCount)

    def handleClientSetCMDRate(self, client, dgi):
        cmdRate = dgi.getUint8()
        client.cmdRate = cmdRate
        client.cmdInterval = 1.0 / cmdRate

    def handleClientSetUpdateRate(self, client, dgi):
        updateRate = dgi.getUint8()
        updateRate = max(sv_minupdaterate.getValue(), min(updateRate, sv_maxupdaterate.getValue()))
        client.updateRate = updateRate
        client.updateInterval = 1.0 / updateRate

    def handleClientHello(self, client, dgi):
        password = dgi.getString()
        dcHash = dgi.getUint32()
        updateRate = dgi.getUint8()
        cmdRate = dgi.getUint8()

        dg = PyDatagram()
        dg.addUint16(NetMessages.SV_Hello_Resp)

        valid = True
        msg = ""
        if password != sv_password.getValue():
            valid = False
            msg = "Incorrect password"
        elif dcHash != self.hashVal:
            valid = False
            msg = "DC hash mismatch"

        dg.addUint8(int(valid))
        if not valid:
            self.notify.warning("Could not verify client %i (%s)" % (client.connection, msg))
            # Client did not verify correctly. Let them know and
            # close them out.
            dg.addString(msg)
            self.sendDatagram(dg, client.connection)
            self.closeClientConnection(client)
            return

        # Make sure the client's requested snapshot rate
        # is within our defined boundaries.
        updateRate = max(sv_minupdaterate.getValue(), min(updateRate, sv_maxupdaterate.getValue()))
        client.updateRate = updateRate
        client.updateInterval = 1.0 / updateRate

        client.cmdRate = cmdRate
        client.cmdInterval = 1.0 / cmdRate
        client.state = ClientState.Verified
        client.id = self.clientIdAllocator.allocate()

        self.notify.info("Got hello from client %i, verified, given ID %i" % (client.connection, client.id))

        # Tell the client their ID and our tick rate.
        dg.addUint16(client.id)
        dg.addUint8(base.ticksPerSec)

        self.sendDatagram(dg, client.connection)

        messenger.send('clientConnected', [client])

    def handleClientDisconnect(self, client):
        # Delete all objects owned by the client
        for do in client.objectsByDoId.values():
            self.deleteObject(do, False)
        client.objectsByDoId = {}
        client.objectsByZoneId = {}
        messenger.send('clientDisconnected', [client])
        self.closeClientConnection(client)

    def __handleNetCallback(self, connection, state, oldState):
        if state == NetworkSystem.NCSConnecting:
            if not self.canAcceptConnection():
                return
            if not self.netSys.acceptConnection(connection):
                self.notify.warning("Couldn't accept connection %i" % connection)
                return
            if not self.netSys.setConnectionPollGroup(connection, self.pollGroup):
                self.notify.warning("Couldn't set poll group on connection %i" % connection)
                self.netSys.closeConnection(connection)
                return
            info = NetworkConnectionInfo()
            self.netSys.getConnectionInfo(connection, info)
            self.handleNewConnection(connection, info)

        elif state == NetworkSystem.NCSClosedByPeer or \
            state == NetworkSystem.NCSProblemDetectedLocally:

            client = self.clientsByConnection[connection]
            self.notify.info("Client %i disconnected" % client.connection)
            self.handleClientDisconnect(client)

    def handleNewConnection(self, connection, info):
        self.notify.info("Got client from %s (connection %i), awaiting hello" % (info.netAddress, connection))
        client = ServerRepository.Client(connection, info.netAddress)
        self.clientsByConnection[connection] = client
