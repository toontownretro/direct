from panda3d.core import URLSpec, NetAddress, SteamNetworkSystem, SteamNetworkMessage
from panda3d.direct import CClientRepository, DCPacker

from direct.distributed.PyDatagram import PyDatagram
from direct.showbase.DirectObject import DirectObject
from direct.directnotify.DirectNotifyGlobal import directNotify

from .ClockDriftManager import ClockDriftManager
from .BaseObjectManager import BaseObjectManager
from .DistributedObject import DistributedObject
from .ClientConfig import *
from .NetMessages import NetMessages
from .DOState import DOState

class ClientRepository(BaseObjectManager, CClientRepository):
    notify = directNotify.newCategory("ClientRepository")

    def __init__(self):
        BaseObjectManager.__init__(self, True)
        CClientRepository.__init__(self)
        self.setPythonRepository(self)

        self.clockDriftMgr = ClockDriftManager()

        self.netSys = SteamNetworkSystem()
        self.connected = False
        self.connectionHandle = None
        self.serverAddress = None
        self.msgType = 0

        self.clientId = 0
        # Server tick count from latest received snapshot.
        self.serverTickCount = 0
        self.serverTickRate = 0
        # Reference server tick count for delta snapshots.  -1 means we have
        # no delta reference and need an absolute update.
        self.deltaTick = -1
        self.serverIntervalPerTick = 0
        self.lastServerTickTime = 0
        self.interestHandle = 0
        self.lastUpdateTime = 0

        # Estimated "ping" time, since the ping query from the client and
        # response from the server.  In milliseconds.
        self.pingLatency = 0
        self.pendingPing = False
        self.pingSendOutTime = 0.0
        self.nextPingTime = 0.0

        self.predictionRandomSeed = 0
        self.predictionPlayer = None

    def sendPing(self):
        """
        Issues a ping query to the server.  The client sends the server a
        "ping" message, and when the server gets the message, it immediately
        sends a response back.  When the client receives the response, it
        measures the total time elapsed.
        """
        if self.pendingPing:
            return
        self.pendingPing = True

        self.pingSendOutTime = globalClock.real_time
        #print("Send ping at", self.pingSendOutTime)
        dg = PyDatagram()
        dg.addUint16(NetMessages.CL_Ping)
        self.sendDatagram(dg)

    def handlePingResponse(self):
        if not self.pendingPing:
            return
        self.pendingPing = False
        now = globalClock.real_time
        # Seconds to milliseconds.
        #print("recv ping resp at", now)
        self.pingLatency = max(0, int((now - self.pingSendOutTime) * 1000.0))
        if cl_report_ping.value:
            self.notify.info("Current ping: %i ms" % self.pingLatency)
        self.nextPingTime = now + cl_ping_interval.value

        # Now inform the server of our ping.
        dg = PyDatagram()
        dg.addUint16(NetMessages.CL_InformPing)
        dg.addUint32(self.pingLatency)
        self.sendDatagram(dg)

    #def simObjects(self, task):
    #    for do in self.doId2do.values():
    #        if not do.predictable:
    #            do.simulate()
    #    return task.cont

    #def updateObjects(self, task):
    #    for do in self.doId2do.values():
    #        if not do.isDODeleted():
    #            do.update()
    #    return task.cont

    def runFrame(self, task):
        self.readerPollUntilEmpty()
        self.runCallbacks()

        # Handle automatic pinging for latency measuring.
        if self.connected and cl_ping.value:
            if globalClock.real_time >= self.nextPingTime:
                self.sendPing()

        return task.cont

    def interpolateObjects(self, task):
        DistributedObject.interpolateObjects()
        return task.cont

    def startClientLoop(self):
        base.simTaskMgr.add(self.runFrame, "clientRunFrame", sort = -100)
        #base.simTaskMgr.add(self.simObjects, "clientSimObjects", sort = 0)
        base.taskMgr.add(self.interpolateObjects, "clientInterpolateObjects", sort = 30)
        #base.taskMgr.add(self.updateObjects, "clientUpdateObjects", sort = 31)

    def stopClientLoop(self):
        base.simTaskMgr.remove("clientRunFrame")
        base.simTaskMgr.remove("clientSimObjects")
        base.taskMgr.remove("clientInterpolateObjects")
        #base.taskMgr.remove("clientUpdateObjects")

    def getNextInterestHandle(self):
        return (self.interestHandle + 1) % 256

    # Change the rate at which we receive state snapshots from the server.
    def setUpdateRate(self, rate):
        dg = PyDatagram()
        dg.addUint16(NetMessages.CL_SetUpdateRate)
        dg.addUint8(rate)
        self.sendDatagram(dg)

    # Change the rate at which we send commands to the server.
    def setCMDRate(self, rate):
        dg = PyDatagram()
        dg.addUint16(NetMessages.CL_SetCMDRate)
        dg.addUint8(rate)
        self.sendDatagram(dg)

    # Request the server to replace our interested zones
    # with this list.
    def setInterest(self, interestZones):
        dg = PyDatagram()
        dg.addUint16(NetMessages.CL_SetInterest)
        handle = self.getNextInterestHandle()
        dg.addUint8(handle)
        dg.addUint8(len(interestZones))
        for i in range(len(interestZones)):
            dg.addUint32(interestZones[i])
        self.sendDatagram(dg)

        return handle

    # Request the server to remove the specified
    # zones from our interest.
    def removeInterest(self, interestZones):
        dg = PyDatagram()
        dg.addUint16(NetMessages.CL_RemoveInterest)
        handle = self.getNextInterestHandle()
        dg.addUint8(handle)
        dg.addUint8(len(interestZones))
        for i in range(len(interestZones)):
            dg.addUint32(interestZones[i])
        self.sendDatagram(dg)

        return handle

    # Request the server to add the specified zone
    # to our interest.
    def addInterest(self, interestZones):
        dg = PyDatagram()
        dg.addUint16(NetMessages.CL_AddInterest)
        handle = self.getNextInterestHandle()
        dg.addUint8(handle)
        dg.addUint8(len(interestZones))
        for i in range(len(interestZones)):
            dg.addUint32(interestZones[i])
        self.sendDatagram(dg)

        return handle

    def __handleInterestComplete(self, dgi):
        handle = dgi.getUint8()
        messenger.send('interestComplete', [handle])

    def sendHello(self, password = ""):
        dg = PyDatagram()
        dg.addUint16(NetMessages.CL_Hello)
        dg.addString(password)
        # DC hash verification
        dg.addUint32(self.hashVal)
        dg.addUint8(cl_updaterate.getValue())
        dg.addUint8(cl_cmdrate.getValue())
        dg.addFloat32(getClientInterpAmount())
        self.sendDatagram(dg)

    def __handleServerHelloResp(self, dgi):
        ret = dgi.getUint8()
        if ret:
            self.clientId = dgi.getUint16()

            self.serverTickRate = dgi.getUint8()
            self.serverIntervalPerTick = 1.0 / self.serverTickRate
            # Use the same simulation rate as the server!
            base.setTickRate(self.serverTickRate)
            tickCount = dgi.getUint32()
            base.resetSimulation(tickCount)

            self.notify.info("Verified with server")
            messenger.send('serverHelloSuccess')
        else:
            self.notify.warning("Failed to verify with server")
            msg = dgi.getString()
            messenger.send('serverHelloFail', [msg])
            self.disconnect()

    def __handleServerTick(self, dgi):
        self.readSnapshotHeaderData(dgi)

        oldTick = self.serverTickCount
        self.serverTickCount = dgi.getUint32()

        isDelta = bool(dgi.getUint8())

        if isDelta and self.deltaTick < 0:
            # We requested a full update but got a delta compressed update.
            # Ignore it.
            self.serverTickCount = oldTick
            return

        self.lastServerTickTime = self.serverTickCount * self.serverIntervalPerTick

        self.clockDriftMgr.setServerTick(self.serverTickCount)

        base.clockMgr.enterSimulationTime(self.serverTickCount)

        self.lastUpdateTime = base.clockMgr.getClientTime()

        if hasattr(self, 'prediction') and hasattr(base, 'localAvatar') and base.localAvatar is not None:
            if True or (base.localAvatar.lastOutgoingCommand == base.localAvatar.commandAck):
                self.runPrediction()

            numExeced = base.localAvatar.commandAck - base.localAvatar.lastCommandAck
            # Copy last set of changes right into current frame.
            self.prediction.preEntityPacketReceived(numExeced, 0)

            if not isDelta:
                self.prediction.onReceivedUncompressedPacket()

        # Let the C++ repository unpack and apply the snapshot onto our objects
        self.unpackServerSnapshot(dgi, isDelta)

        if hasattr(self, 'prediction'):
            self.prediction.postEntityPacketReceived()

        self.postSnapshot()

        # Restore the true client tick count and frame time.
        base.clockMgr.exitSimulationTime()

        self.notify.debug("Got tick %i and snapshot from server" % self.serverTickCount)

        if (self.deltaTick >= 0) or not isDelta:
            # We have a new delta reference.
            self.deltaTick = self.serverTickCount

    def readSnapshotHeaderData(self, dgi):
        pass

    def postSnapshot(self):
        pass

    def sendTick(self):
        # Inform server we got the tick
        dg = PyDatagram()
        dg.addUint16(NetMessages.CL_Tick)
        dg.addInt32(self.deltaTick)
        dg.addFloat32(globalClock.getDt())
        self.sendDatagram(dg)

    def __handleGenerateOwnerObject(self, dgi):
        generated = []

        while dgi.getRemainingSize() > 0:
            classId = dgi.getUint16()
            doId = dgi.getUint32()
            zoneId = dgi.getUint32()
            hasState = dgi.getUint8()
            dclass = self.dclassesByNumber[classId]
            classDef = dclass.getOwnerClassDef()
            if not classDef:
                classDef = dclass.getClassDef()

            if not classDef:
                self.notify.error("No classDef for dclass %s" % dclass.getName())

            do = classDef()
            do.doId = doId
            do.zoneId = zoneId
            do.dclass = dclass
            do.isOwner = True
            self.doId2do[do.doId] = do
            self.addObject(do)

            assert self.notify.debug("Generate owner " + repr(classDef) + " with doId " + str(doId) + " in zone " + str(zoneId) + " dclass " + repr(dclass))

            do.generate()
            assert do.isDOGenerated()

            generated.append((do, hasState))

            if hasState:
                self.notify.debug("Unpacking baseline/initial owner object state")
                do.preDataUpdate()
                # An initial state was supplied for the object.
                # Unpack it in the C++ repository.
                self.unpackObjectState(dgi, doId)

        # Now that all new objects are generated with an initial
        # state applied, call postDataUpdate() and announceGenerate() on
        # them.
        for do, hasState in generated:
            if hasState:
                do.postDataUpdate()
            do.announceGenerate()
            assert do.isDOAlive()

    def __handleGenerateObject(self, dgi):
        generated = []

        while dgi.getRemainingSize() > 0:
            classId = dgi.getUint16()
            doId = dgi.getUint32()
            zoneId = dgi.getUint32()
            hasState = dgi.getUint8()
            dclass = self.dclassesByNumber[classId]
            classDef = dclass.getClassDef()

            do = classDef()
            do.doId = doId
            do.zoneId = zoneId
            do.dclass = dclass
            self.doId2do[do.doId] = do
            self.addObject(do)

            assert self.notify.debug("Generate " + repr(classDef) + " with doId " + str(doId) + " in zone " + str(zoneId) + " dclass " + repr(dclass))

            do.generate()
            assert do.isDOGenerated()

            generated.append((do, hasState))

            if hasState:
                self.notify.debug("Unpacking baseline/initial object state")
                do.preDataUpdate()
                # An initial state was supplied for the object.
                # Unpack it in the C++ repository.
                self.unpackObjectState(dgi, doId)

        # Now that all new objects are generated with an initial
        # state applied, call postDataUpdate() and announceGenerate() on
        # them.
        for do, hasState in generated:
            if hasState:
                do.postDataUpdate()
            do.announceGenerate()
            assert do.isDOAlive()

    def __handleDeleteObject(self, dgi):
        while dgi.getRemainingSize() > 0:
            doId = dgi.getUint32()
            do = self.doId2do.get(doId, None)
            if not do:
                continue
            self.deleteObject(do)

    def deleteObject(self, do):
        self.removeObject(do.doId)
        if do in self.doId2do.values():
            del self.doId2do[do.doId]
        elif do in self.doId2ownerView.values():
            del self.doId2ownerView[do.doId]
        if do.doState > DOState.Disabled:
            do.disable()
            assert do.isDODisabled()
        do.delete()
        assert do.isDODeleted()

    def deleteAllObjects(self):
        # Delete objects in the reverse order they were generated.
        for do in reversed(list(self.doId2do.values())):
            self.removeObject(do.doId)
            if do.doState > DOState.Disabled:
                do.disable()
                assert do.isDODisabled()
            do.delete()
            assert do.isDODeleted()

        self.doId2do = {}
        # We don't use this, so there shouldn't be anything in it.
        assert len(self.doId2ownerView) == 0
        self.doId2ownerView = {}

    def disconnect(self):
        if not self.connected:
            return

        self.notify.info("Disconnecting from server")
        self.serverAddress = None
        if self.connectionHandle:
            self.netSys.closeConnection(self.connectionHandle)
            self.connectionHandle = None
        self.connected = False
        self.pendingPing = False
        self.clientId = 0
        self.serverTickRate = 0
        self.serverIntervalPerTick = 0
        self.stopClientLoop()
        self.deleteAllObjects()

    def readerPollUntilEmpty(self):
        if not self.connected:
            return

        while self.readerPollOnce():
            pass

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

    def readerPollOnce(self):
        if not self.connected:
            return False

        assert self.connectionHandle

        msg = SteamNetworkMessage()
        if self.netSys.receiveMessageOnConnection(self.connectionHandle, msg):
            self.msgType = msg.getDatagramIterator().getUint16()
            self.handleDatagram(msg.getDatagramIterator())
            return True

        return False

    def sendDatagram(self, dg, reliable = True):
        if dg.getLength() <= 0 or not self.connected:
            return
        if reliable:
            sendType = SteamNetworkSystem.NSFReliableNoNagle
        else:
            sendType = SteamNetworkSystem.NSFUnreliableNoDelay
        self.netSys.sendDatagram(self.connectionHandle, dg, sendType)

    def connect(self, url):
        self.notify.info("Attemping to connect to %s" % (url))
        urlSpec = URLSpec(url)
        addr = NetAddress()
        addr.setHost(urlSpec.getServer(), urlSpec.getPort())
        self.serverAddress = addr
        self.connectionHandle = self.netSys.connectByIPAddress(addr)
        if not self.connectionHandle:
            messenger.send('connectFailure', [self.serverAddress])
            self.serverAddress = None
            self.connectionHandle = None
        else:
            self.startClientLoop()

        # Wait for the callback to determine if connection succeeded

    def __handleNetCallback(self, connection, state, oldState):
        # Connection state has changed.

        if connection != self.connectionHandle:
            # I don't think this is possible.. but just in case.
            return

        if state == SteamNetworkSystem.NCSConnected:
            # We've successfully connected.
            self.connected = True
            self.notify.info("Successfully connected to %s" % self.serverAddress)
            messenger.send('connectSuccess', [self.serverAddress])

        elif oldState == SteamNetworkSystem.NCSConnecting:
            # If state was connecting and new state is not connected, we failed!
            self.connected = False
            self.stopClientLoop()
            messenger.send('connectFailure', [self.serverAddress])
            self.notify.warning("Failed to connect to %s" % self.serverAddress)
            self.serverAddress = None

        elif state == SteamNetworkSystem.NCSClosedByPeer or \
            state == SteamNetworkSystem.NCSProblemDetectedLocally:

            # Lost connection
            self.connected = False
            self.notify.warning("Lost connection to server")
            messenger.send('connectionLost')
            self.serverAddress = None
            self.connectionHandle = None
            self.pendingPing = False
            self.stopClientLoop()
            self.deleteAllObjects()

    def handleDatagram(self, dgi):
        if self.msgType == NetMessages.SV_Hello_Resp:
            self.__handleServerHelloResp(dgi)
        elif self.msgType == NetMessages.SV_InterestComplete:
            self.__handleInterestComplete(dgi)
        elif self.msgType == NetMessages.SV_Tick:
            self.__handleServerTick(dgi)
        elif self.msgType == NetMessages.SV_GenerateObject:
            self.__handleGenerateObject(dgi)
        elif self.msgType == NetMessages.SV_GenerateOwnerObject:
            self.__handleGenerateOwnerObject(dgi)
        elif self.msgType == NetMessages.SV_DeleteObject:
            self.__handleDeleteObject(dgi)
        elif self.msgType == NetMessages.B_ObjectMessage:
            self.__handleObjectMessage(dgi)
        elif self.msgType == NetMessages.SV_Ping_Resp:
            self.handlePingResponse()

    def sendUpdate(self, do, name, args):
        if not do:
            return
        if not do.dclass:
            return

        field = do.dclass.getFieldByName(name)
        if not field:
            self.notify.warning("Tried to send update for non-existent field %s" % name)
            return

        if field.asParameter():
            self.notify.warning("Tried to send parameter field as a message")
            return

        # The field must be marked as `clsend` in the DC file for the client
        # to be able to send this message.  The AI will double-check that the
        # field is clsend before unpacking the message, in case a modified
        # client removes this check.
        #if not field.isClsend():
        #    self.notify.warning("Tried to send a non-clsend message! Field %s" % name)
        #    self.disconnect()
        #    return

        packer = DCPacker()
        packer.rawPackUint16(NetMessages.B_ObjectMessage)
        packer.rawPackUint32(do.doId)
        packer.rawPackUint16(field.getNumber())

        packer.beginPack(field)
        field.packArgs(packer, args)
        if not packer.endPack():
            self.notify.warning("Failed to pack object message")
            return

        dg = PyDatagram(packer.getBytes())
        self.sendDatagram(dg, reliable = not field.hasKeyword("unreliable"))

    def __handleObjectMessage(self, dgi):
        doId = dgi.getUint32()
        do = self.doId2do.get(doId)
        if not do:
            self.notify.warning("Received message for unknown object %i" % doId)
            return

        fieldNumber = dgi.getUint16()
        field = do.dclass.getFieldByIndex(fieldNumber)
        if not field:
            self.notify.warning("Received message on unknown field %i on object %i" % (fieldNumber, doId))
            return

        if field.asParameter():
            self.notify.warning("Received message for parameter field?")
            return

        # We can safely pass this message onto the object
        packer = DCPacker()
        packer.setUnpackData(dgi.getRemainingBytes())
        packer.beginUnpack(field)
        field.receiveUpdate(packer, do)
        if not packer.endUnpack():
            self.notify.warning("Failed to unpack message")
