from panda3d.bsp import NetworkSystem, NetworkCallbacks, NetworkMessage, NetworkConnectionInfo
from panda3d.core import URLSpec, NetAddress
from panda3d.direct import CClientRepository, DCPacker

from direct.distributed.PyDatagram import PyDatagram
from direct.showbase.DirectObject import DirectObject
from direct.directnotify.DirectNotifyGlobal import directNotify

from .BaseObjectManager import BaseObjectManager
from .ClientConfig import *
from .NetMessages import NetMessages
from .DOState import DOState

class ClientRepository(BaseObjectManager, CClientRepository):
    notify = directNotify.newCategory("ClientRepository")

    def __init__(self):
        BaseObjectManager.__init__(self, True)
        CClientRepository.__init__(self)
        self.setPythonRepository(self)

        self.netSys = NetworkSystem()
        self.netCallbacks = NetworkCallbacks()
        self.netCallbacks.setCallback(self.__handleNetCallback)
        self.connected = False
        self.connectionHandle = None
        self.serverAddress = None
        self.msgType = 0

        self.clientId = 0
        self.serverTickCount = 0
        self.serverTickRate = 0
        self.serverIntervalPerTick = 0
        self.interestHandle = 0

    def simObjects(self):
        for do in self.doId2do.values():
            do.update()

    def runFrame(self, task):
        self.readerPollUntilEmpty()
        self.runCallbacks()

        self.simObjects()

        return task.cont

    def startClientLoop(self):
        base.simTaskMgr.add(self.runFrame, "clientRunFrame", sort = -100)

    def stopClientLoop(self):
        base.simTaskMgr.remove("clientRunFrame")

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
        self.sendDatagram(dg)

    def __handleServerHelloResp(self, dgi):
        ret = dgi.getUint8()
        if ret:
            self.clientId = dgi.getUint16()

            self.serverTickRate = dgi.getUint8()
            self.serverIntervalPerTick = 1.0 / self.serverTickRate
            # Use the same simulation rate as the server!
            base.setTickRate(self.serverTickRate)

            self.notify.info("Verified with server")
            messenger.send('serverHelloSuccess')
        else:
            self.notify.warning("Failed to verify with server")
            msg = dgi.getString()
            messenger.send('serverHelloFail', [msg])
            self.disconnect()

    def __handleServerTick(self, dgi):
        self.serverTickCount = dgi.getUint32()

        # Let the C++ repository unpack and apply the snapshot onto our objects
        self.unpackServerSnapshot(dgi)

        self.notify.debug("Got tick %i and snapshot from server" % self.serverTickCount)

        # Inform server we got the tick
        dg = PyDatagram()
        dg.addUint16(NetMessages.CL_Tick)
        dg.addUint32(self.serverTickCount)
        self.sendDatagram(dg)

    def __handleGenerateOwnerObject(self, dgi):
        while dgi.getRemainingSize() > 0:
            classId = dgi.getUint16()
            doId = dgi.getUint32()
            zoneId = dgi.getUint32()
            hasState = dgi.getUint8()
            dclass = self.dclassesByNumber[classId]
            classDef = dclass.getOwnerClassDef()

            do = classDef()
            do.doId = doId
            do.zoneId = zoneId
            do.dclass = dclass
            self.doId2do[do.doId] = do

            do.generate()

            if hasState:
                self.notify.debug("Unpacking baseline/initial owner object state")
                # An initial state was supplied for the object
                # Unpack it in the C++ repository.
                self.unpackObjectState(dgi, do, dclass, doId)

            do.announceGenerate()

    def __handleGenerateObject(self, dgi):
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

            do.generate()

            if hasState:
                self.notify.debug("Unpacking baseline/initial object state")
                # An initial state was supplied for the object
                # Unpack it in the C++ repository.
                self.unpackObjectState(dgi, do, dclass, doId)

            do.announceGenerate()

    def __handleDeleteObject(self, dgi):
        while dgi.getRemainingSize() > 0:
            doId = dgi.getUint32()
            do = self.doId2do.get(doId, None)
            if not do:
                continue
            self.deleteObject(do)

    def deleteObject(self, do):
        del self.doId2do[do.doId]
        if do.doState > DOState.Disabled:
            do.disable()
        do.delete()

    def deleteAllObjects(self):
        for do in self.doId2do.values():
            if do.doState > DOState.Disabled:
                do.disable()
            do.delete()

        self.doId2do = {}

    def disconnect(self):
        if not self.connected:
            return

        self.notify.info("Disconnecting from server")
        self.serverAddress = None
        if self.connectionHandle:
            self.netSys.closeConnection(self.connectionHandle)
            self.connectionHandle = None
        self.connected = False
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
        self.netSys.runCallbacks(self.netCallbacks)

    def readerPollOnce(self):
        msg = NetworkMessage()
        if self.netSys.receiveMessageOnConnection(self.connectionHandle, msg):
            self.msgType = msg.getDatagramIterator().getUint16()
            self.handleDatagram(msg.getDatagramIterator())
            return True
        return False

    def sendDatagram(self, dg):
        if dg.getLength() <= 0 or not self.connected:
            return
        self.netSys.sendDatagram(self.connectionHandle, dg, NetworkSystem.NSFReliableNoNagle)

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

        if state == NetworkSystem.NCSConnected:
            # We've successfully connected.
            self.connected = True
            self.notify.info("Successfully connected")
            messenger.send('connectSuccess', [self.serverAddress])

        elif oldState == NetworkSystem.NCSConnecting:
            # If state was connecting and new state is not connected, we failed!
            self.connected = False
            self.stopClientLoop()
            messenger.send('connectFailure', [self.serverAddress])
            self.serverAddress = None

        elif state == NetworkSystem.NCSClosedByPeer or \
            state == NetworkSystem.NCSProblemDetectedLocally:

            # Lost connection
            self.connected = False
            self.notify.warning("Lost connection to server")
            messenger.send('connectionLost')
            self.serverAddress = None
            self.connectionHandle = None
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
        self.sendDatagram(dg)

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
