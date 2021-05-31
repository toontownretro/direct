from .BaseDistributedObject import BaseDistributedObject

from panda3d.direct import *

from .ClientConfig import *

class InterpVarEntry:

    def __init__(self, var, getter, setter, flags, arrayIndex):
        self.var = var
        self.getter = getter
        self.setter = setter
        self.arrayIndex = arrayIndex
        self.flags = flags
        self.needsInterpolation = False

# Base client network object
class DistributedObject(BaseDistributedObject):

    SimulationVar = 1 << 0
    AnimationVar = 1 << 1

    neverDisable = False

    InterpolateList = []
    TeleportList = []

    def __init__(self):
        BaseDistributedObject.__init__(self)
        #self.interpGroup = CInterpolatedGroup()
        self.oldSimulationTime = 0.0
        self.isOwner = False
        self.interpVars = []
        self.lastInterpolationTime = 0.0

    @staticmethod
    def interpolateObjects():
        #print("interpolate at", globalClock.getFrameTime())
        ctx = InterpolationContext()
        ctx.enableExtrapolation(True)
        ctx.setLastTimestamp(base.cr.lastServerTickTime)
        for do in DistributedObject.InterpolateList:
            do.interpolate(globalClock.getFrameTime())
            do.postInterpolate()

    def addInterpolatedVar(self, var, getter, setter,
                           flags = SimulationVar,
                           arrayIndex = -1):
        var.setInterpolationAmount(self.getInterpolateAmount())
        self.interpVars.append(InterpVarEntry(var, getter, setter, flags, arrayIndex))

    def removeInterpolatedVar(self, var):
        entry = None
        for ent in self.interpVars:
            if ent.var == var:
                entry = ent
                break
        if entry is not None:
            self.interpVars.remove(entry)

    def RecvProxy_simulationTime(self, addT):
        # Note, this needs to be encoded relative to the packet timestamp, not
        # raw client clock.
        tickBase = base.getNetworkBase(base.tickCount, self.doId)
        t = tickBase
        # and then go back to floating point time
        t += addT # Add in an additional up to 256 100ths from the server.

        # Center self.simulationTime around current time.
        while t < base.tickCount - 127:
            t += 256
        while t > base.tickCount + 127:
            t -= 256

        self.simulationTime = t * base.intervalPerTick

    def isSimulationChanged(self):
        return self.simulationTime != self.oldSimulationTime

    def isPredictable(self):
        return False

    def shouldInterpolate(self):
        return True

    def preDataUpdate(self):
        """
        Override this method to do stuff before a state snapshot is unpacked
        onto the object.
        """

        # Restore all of our interpolated variables to the most recently
        # networked value.  This way if the value does not change in the new
        # snapshot, we record the networked value, and not the most recently
        # interpolated value.
        for entry in self.interpVars:
            if entry.arrayIndex != -1:
                entry.setter(entry.arrayIndex, entry.var.getLastNetworkedValue())
            else:
                entry.setter(entry.var.getLastNetworkedValue())

    def getInterpolateAmount(self):
        serverTickMultiple = 1
        return base.ticksToTime(base.timeToTicks(getClientInterpAmount()) + serverTickMultiple)

    def getLastChangedTime(self, flags):
        if flags & DistributedObject.SimulationVar:
            if self.simulationTime == 0.0:
                return base.frameTime
            else:
                return self.simulationTime

        return base.frameTime

    def postInterpolate(self):
        """
        Called after the object has been interpolated.
        """
        pass

    def onLatchInterpolatedVars(self, changeTime, flags):
        """
        Override this method to record values of interpolated variables with
        the timestamp passed in.
        """

        for entry in self.interpVars:
            if not (entry.flags & flags):
                continue

            if entry.arrayIndex != -1:
                val = entry.getter(entry.arrayIndex)
            else:
                val = entry.getter()
            if entry.var.recordValue(val, changeTime, True):
                # Value is changed, we need to interpolate it.
                entry.needsInterpolation = True

        if self.shouldInterpolate():
            self.addToInterpolationList()

    def onStoreLastNetworkedValue(self):
        for entry in self.interpVars:
            if entry.arrayIndex != -1:
                val = entry.getter(entry.arrayIndex)
            else:
                val = entry.getter()
            entry.var.recordLastNetworkedValue(val, base.frameTime)

    def interpolate(self, now):
        done = True
        if now < self.lastInterpolationTime:
            for entry in self.interpVars:
                entry.needsInterpolation = True

        self.lastInterpolationTime = now

        for entry in self.interpVars:
            if not entry.needsInterpolation:
                continue

            if entry.var.interpolate(now):
                entry.needsInterpolation = False
            else:
                done = False

            if entry.arrayIndex != -1:
                entry.setter(entry.arrayIndex, entry.var.getInterpolatedValue())
            else:
                entry.setter(entry.var.getInterpolatedValue())

        if done:
            self.removeFromInterpolationList()

    def addToInterpolationList(self):
        if not self in DistributedObject.InterpolateList:
            DistributedObject.InterpolateList.append(self)

    def removeFromInterpolationList(self):
        if self in DistributedObject.InterpolateList:
            DistributedObject.InterpolateList.remove(self)

    def postDataUpdate(self):
        """
        Override this method to do stuff after a state snapshot has been
        unpacked onto the object.
        """

        simChanged = self.isSimulationChanged()
        if not self.isPredictable():
            if simChanged:
                self.onLatchInterpolatedVars(
                    self.getLastChangedTime(DistributedObject.SimulationVar),
                    DistributedObject.SimulationVar)
        else:
            self.onStoreLastNetworkedValue()
        self.oldSimulationTime = self.simulationTime

    def sendUpdate(self, name, args = []):
        """
        Sends a non-stateful event message from one object view to another.
        """
        base.cl.sendUpdate(self, name, args)

    def announceGenerate(self):
        """ Called when the object is coming into existence *after* the
        baseline state has been applied, or when the object was disabled and
        it is coming back. """

        pass

    def disable(self):
        """ Called when the object is being temporarily removed/cached away.
        only clean up logical things and remove it from the scene graph, but
        don't tear anything down, because it might come back later via
        announceGenerate(). """

        self.removeFromInterpolationList()
        self.ignoreAll()
        self.removeAllTasks()

    def delete(self):
        self.interpVars = None
        BaseDistributedObject.delete(self)
