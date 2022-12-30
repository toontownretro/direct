from panda3d.core import UniqueIdAllocator, HashVal, SteamNetworkSystem, SteamNetworkMessage, SteamNetworkConnectionInfo
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
    """
    This class implements the core functionality of the server.  It keeps track
    of all distributed objects and clients in the world and manages sending
    state updates to interested clients.
    """

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

            # Last instantaneous RTT value from client.
            self.currentRtt = 0
            # Sliding window average.
            self.averageRtt = 0
            self.rttWindowSize = 5
            self.rttSlidingWindow = [0] * self.rttWindowSize

            self.interpAmount = 0.0

            # What tick are they currently on?
            self.prevTickCount = 0
            self.dt = 0
            self.tickRemainder = 0
            self.tickCount = 0
            # Delta reference tick.
            self.deltaTick = -1

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
        self.netSys = SteamNetworkSystem()
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
        base.simTaskMgr.add(self.simObjectsTask, "serverSimObjects", sort = 0)
        base.simTaskMgr.add(self.takeSnapshotTask, "serverTakeSnapshot", sort = 100)

    def getMaxClients(self):
        return sv_max_clients.getValue()

    def allocateObjectID(self):
        return self.objectIdAllocator.allocate()

    def freeObjectID(self, id):
        self.objectIdAllocator.free(id)

    # Generate a distributed object on the network
    # Can be given a client owner, in which that client will generate an
    # owner-view instance of the object.
    def generateObject(self, do, zoneId, owner = None, announce = True):
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
        assert do.isDOGenerated()

        clients = set(self.zonesToClients.get(do.zoneId, set()))
        if owner and clients:
            # Don't include the owner in this message, we send a specific
            # generate for the owner.
            clients -= set([owner])

        if clients:
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

        if announce:
            do.announceGenerate()
            assert do.isDOAlive()

    def deleteObject(self, do, removeFromOwnerTable = True):
        if do.isDODeleted():
            assert do.doId not in self.doId2do
            return

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
        assert do.isDODeleted()

    def simObjects(self):
        dos = list(self.doId2do.values())
        for do in dos:
            # This DO may have been deleted during a simulation run for a
            # previous DO.
            if not do.isDODeleted():
                do.simulate()

    def simObjectsTask(self, task):
        self.simObjects()
        return task.cont

    def runFrame(self, task):
        self.readerPollUntilEmpty()
        self.runCallbacks()

        return task.cont

    def clientNeedsUpdate(self, client):
        return client.isVerified() and client.nextUpdateTime <= globalClock.getFrameTime()

    ###########################################################
    #
    # Snapshot/object packing code
    #
    ###########################################################

    def takeSnapshotTask(self, task):
        self.takeTickSnapshot(base.tickCount)
        return task.cont

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
            oldFrame = client.getClientFrame(client.deltaTick)

            client.lastSnapshot = snap

            dg = PyDatagram()
            dg.addUint16(NetMessages.SV_Tick)
            self.addSnapshotHeaderData(dg, client)
            if oldFrame:
                # We have an old frame to delta against
                self.snapshotMgr.clientFormatDeltaSnapshot(dg, oldFrame.getSnapshot(), snap, list(client.currentInterestZoneIds))
            else:
                self.snapshotMgr.clientFormatSnapshot(dg, snap, list(client.currentInterestZoneIds))
            self.sendDatagram(dg, client.connection)

    def addSnapshotHeaderData(self, dg, client):
        """
        Appends additional show-specific data to the snapshot header for this
        client.
        """
        pass

    def isFull(self):
        return self.numClients >= sv_max_clients.getValue()

    def canAcceptConnection(self):
        return True

    def runCallbacks(self):
        # This will fill up a list of connection events for us to process
        # below.
        self.netSys.runCallbacks()

        # Process the events.
        event = self.netSys.getNextEvent()
        while event:
            self.__handleNetCallback(event.getConnection(),
                event.getState(), event.getOldState())
            event = self.netSys.getNextEvent()

    def readerPollUntilEmpty(self):
        while self.readerPollOnce():
            pass

    def readerPollOnce(self):
        msg = SteamNetworkMessage()
        if self.netSys.receiveMessageOnPollGroup(self.pollGroup, msg):
            self.handleDatagram(msg)
            return True
        return False

    def ensureDatagramSize(self, n, dgi, client):
        """
        Ensures that there at least n bytes remaining in the datagram to unpack
        from the client's message.  If not, the server should not continue on with
        the message.
        """
        if dgi.getRemainingSize() < n:
            self.notify.warning("Truncated message from client %i" % client.connection)
            self.closeClientConnection(client)
            return False
        return True

    def handleDatagram(self, msg):
        datagram = msg.getDatagram()
        connection = msg.getConnection()
        dgi = msg.getDatagramIterator()
        client = self.clientsByConnection.get(connection)

        if not client:
            self.notify.warning("SECURITY: received message from unknown source %i" % connection)
            return

        if not self.ensureDatagramSize(2, dgi, client):
            return
        type = dgi.getUint16()

        self.clientSender = client

        if client.state == ClientState.Unverified:
            # In the unverified (just connected) client state, the only
            # message the client can send is the hello message to get verified
            # and signed onto the server.
            if type == NetMessages.CL_Hello:
                self.handleClientHello(client, dgi)
            else:
                self.notify.warning("SUSPICIOUS: client %i sent unknown message %i in unverified state" % (client.connection, type))
                self.closeClientConnection(client)

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
            elif type == NetMessages.CL_Ping:
                self.handleClientPing(client)
            elif type == NetMessages.CL_InformPing:
                self.handleClientInformPing(client, dgi)
            else:
                self.notify.warning("SUSPICIOUS: client %i sent unknown message %i in verified state" % (client.connection, type))
                self.closeClientConnection(client)

    def handleClientPing(self, client):
        dg = PyDatagram()
        dg.addUint16(NetMessages.SV_Ping_Resp)
        self.sendDatagram(dg, client.connection)

    def handleClientInformPing(self, client, dgi):
        rtt = dgi.getUint32()
        client.currentRtt = rtt
        if client.averageRtt == 0:
            # First rtt report, duplicate to entire window.
            client.rttSlidingWindow = [rtt] * client.rttWindowSize
        else:
            client.rttSlidingWindow = [rtt] + client.rttSlidingWindow[:client.rttWindowSize - 1]
        total = 0
        for rtt in client.rttSlidingWindow:
            total += rtt
        client.averageRtt = total / client.rttWindowSize
        assert self.notify.debug("Client " + str(client.connection) + " average RTT: " + str(client.averageRtt))

    def sendUpdate(self, do, name, args, client = None, excludeClients = []):
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

        reliable = not field.hasKeyword("unreliable")

        dg = PyDatagram(packer.getBytes())
        if not client:
            if field.isBroadcast():
                # Send to all interested clients
                for cl in self.zonesToClients.get(do.zoneId, set()):
                    if cl in excludeClients:
                        continue
                    self.sendDatagram(dg, cl.connection, reliable)
            elif field.isOwnrecv():
                # If the field is an ownrecv without an explicit target client,
                # implicitly send to owner client.
                if not do.owner:
                    self.notify.warning("Can't implicitly send ownrecv message to owner with no owner client")
                    return
                self.sendDatagram(dg, do.owner.connection, reliable)
            else:
                self.notify.warning("Can't send non-broadcast and non-ownrecv object message without a target client")
                return
        else:
            self.sendDatagram(dg, client.connection, reliable)

    def handleObjectMessage(self, client, dgi):
        """
        Receives a message sent on a distributed object by a client.  Does a
        bunch of security and sanity checks before actually unpacking the
        contents of the message and passing it onto the object.  The field
        must be a method in the DC file and marked with the 'clsend' keyword.

        Messages are used for RPC-like communication between client and server
        views of a distributed object.  Object messages can only be sent
        between the server and client.  The client cannot send messages to
        other clients, only the server.  Object messages in the DC file are
        implicitly server-send only unless explicitly marked 'clsend'.
        (server only) If the field is marked 'broadcast', the message will be
        sent to all clients that have interest in the object's location.
        """

        # Make sure the message has the doId (4 bytes) and the field number
        # (2 bytes).
        if not self.ensureDatagramSize(6, dgi, client):
            return

        doId = dgi.getUint32()

        do = self.doId2do.get(doId)
        if not do:
            self.notify.warning("SUSPICIOUS: client %i tried to send message to unknown doId %i" %
                                (client.id, doId))
            return

        if not do.dclass:
            return

        # The client must have interest in the object's location to be able to
        # send the message.  If the client is not interested in the object's
        # location, the object would not be in the client's doId2do table, so
        # there's no way the client could send a message to this object unless
        # the client is modified.
        if not do.zoneId in client.currentInterestZoneIds:
            self.notify.warning("SUSPICIOUS: client %i tried to send message to an object "
                                "whose zone ID is not in the client interest zones." % client.id)
            return

        fieldNumber = dgi.getUint16()
        field = do.dclass.getFieldByIndex(fieldNumber)
        if not field:
            self.notify.warning("SUSPICIOUS: client %i tried to send message on unknown field %i on doId %i" %
                                (client.id, fieldNumber, doId))
            return

        if field.asParameter():
            self.notify.warning("SUSPICIOUS: client %i tried to send message on a parameter field!" % client.id)
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

        if not self.ensureDatagramSize(2, dgi, client):
            return
        handle = dgi.getUint8()
        numZones = dgi.getUint8()

        i = 0
        while i < numZones and dgi.getRemainingSize() >= 4:
            zoneId = dgi.getUint32()
            client.explicitInterestZoneIds.add(zoneId)
            i += 1

        self.updateClientInterestZones(client)
        self.sendInterestComplete(client, handle)

    def handleClientRemoveInterest(self, client, dgi):
        """ Called when client wants to remove interest from a set of zones """

        if not self.ensureDatagramSize(2, dgi, client):
            return
        handle = dgi.getUint8()
        numZones = dgi.getUint8()

        i = 0
        while i < numZones and dgi.getRemainingSize() >= 4:
            zoneId = dgi.getUint32()
            if zoneId in client.explicitInterestZoneIds:
                client.explicitInterestZoneIds.remove(zoneId)
            i += 1

        self.updateClientInterestZones(client)
        self.sendInterestComplete(client, handle)

    def handleClientSetInterest(self, client, dgi):
        """ Called when client wants to completely replace its interest zones """

        if not self.ensureDatagramSize(2, dgi, client):
            return

        client.explicitInterestZoneIds = set()

        handle = dgi.getUint8()
        numZones = dgi.getUint8()

        i = 0
        while i < numZones and dgi.getRemainingSize() >= 4:
            zoneId = dgi.getUint32()
            client.explicitInterestZoneIds.add(zoneId)
            i += 1

        self.updateClientInterestZones(client)
        self.sendInterestComplete(client, handle)

    def packObjectGenerate(self, dg, object):
        dg.addUint16(object.dclass.getNumber())
        dg.addUint32(object.doId)
        dg.addUint32(object.zoneId)

        assert self.notify.debug("Packing generate for " + repr(object))

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

    def sendDatagram(self, dg, connection, reliable = True):
        if reliable:
            sendType = SteamNetworkSystem.NSFReliableNoNagle
        else:
            sendType = SteamNetworkSystem.NSFUnreliableNoDelay
        self.netSys.sendDatagram(connection, dg, sendType)

    def closeClientConnection(self, client):
        if client.id != -1:
            self.clientIdAllocator.free(client.id)
        if client.state == ClientState.Verified:
            self.numClients -= 1
        self.netSys.closeConnection(client.connection)
        del self.clientsByConnection[client.connection]

    def handleClientTick(self, client, dgi):
        # delta tick (4 bytes) and dt (4 bytes)
        if not self.ensureDatagramSize(8, dgi, client):
            return
        client.prevTickCount = int(client.tickCount)
        client.deltaTick = dgi.getInt32()
        client.dt = dgi.getFloat32()
        self.notify.debug("Client acknowleged tick %i" % client.deltaTick)

    def handleClientSetCMDRate(self, client, dgi):
        if not self.ensureDatagramSize(1, dgi, client):
            return
        cmdRate = dgi.getUint8()
        client.cmdRate = cmdRate
        client.cmdInterval = 1.0 / cmdRate

    def handleClientSetUpdateRate(self, client, dgi):
        if not self.ensureDatagramSize(1, dgi, client):
            return
        updateRate = dgi.getUint8()
        updateRate = max(sv_minupdaterate.getValue(), min(updateRate, sv_maxupdaterate.getValue()))
        client.updateRate = updateRate
        client.updateInterval = 1.0 / updateRate

    def handleClientHello(self, client, dgi):

        # Must have the 2 byte string length.
        if not self.ensureDatagramSize(2, dgi, client):
            return
        password = dgi.getString()

        # And now make sure we have the remaining data.
        if not self.ensureDatagramSize(10, dgi, client):
            return
        dcHash = dgi.getUint32()
        updateRate = dgi.getUint8()
        cmdRate = dgi.getUint8()
        interpAmount = dgi.getFloat32()

        dg = PyDatagram()
        dg.addUint16(NetMessages.SV_Hello_Resp)

        valid = True
        msg = ""
        if self.isFull():
            valid = False
            msg = "Server is full"
        elif password != sv_password.getValue():
            valid = False
            msg = "Incorrect password"
        elif dcHash != self.hashVal:
            valid = False
            msg = "DC hash mismatch"
        elif client.state == ClientState.Verified:
            # Prevent them from sending hello more than once.
            valid = False
            msg = "Already signed in"

        dg.addUint8(int(valid))
        if not valid:
            self.notify.warning("Could not verify client %i (%s)" % (client.connection, msg))
            # Client did not verify correctly.  Let them know and
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
        client.interpAmount = interpAmount

        client.cmdRate = cmdRate
        client.cmdInterval = 1.0 / cmdRate
        client.state = ClientState.Verified
        client.id = self.clientIdAllocator.allocate()

        self.notify.info("Got hello from client %i, verified, given ID %i" % (client.connection, client.id))
        self.notify.info("Client lerp time", interpAmount)

        # Tell the client their ID and our tick rate.
        dg.addUint16(client.id)
        dg.addUint8(base.ticksPerSec)
        dg.addUint32(base.tickCount)

        self.numClients += 1

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
        if state == SteamNetworkSystem.NCSConnecting:
            if not self.canAcceptConnection():
                return
            if not self.netSys.acceptConnection(connection):
                self.notify.warning("Couldn't accept connection %i" % connection)
                return
            if not self.netSys.setConnectionPollGroup(connection, self.pollGroup):
                self.notify.warning("Couldn't set poll group on connection %i" % connection)
                self.netSys.closeConnection(connection)
                return
            info = SteamNetworkConnectionInfo()
            self.netSys.getConnectionInfo(connection, info)
            self.handleNewConnection(connection, info)

        elif state == SteamNetworkSystem.NCSClosedByPeer or \
            state == SteamNetworkSystem.NCSProblemDetectedLocally:

            client = self.clientsByConnection.get(connection)
            if not client:
                self.notify.info("Connection %i disconnected but wasn't a recorded client, ignoring " % connection)
                return
            self.notify.info("Client %i disconnected" % client.connection)
            self.handleClientDisconnect(client)

    def handleNewConnection(self, connection, info):
        self.notify.info("Got client from %s (connection %i), awaiting hello" % (info.getNetAddress(), connection))
        client = ServerRepository.Client(connection, info.getNetAddress())
        self.clientsByConnection[connection] = client
