from .BaseDistributedObject import BaseDistributedObject

from panda3d.direct import *
from panda3d.core import *

from .ClientConfig import *
from .DOState import DOState

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
    OmitUpdateLastNetworked = 1 << 2
    ExcludeAutoLatch = 1 << 3
    ExcludeAutoInterpolate = 1 << 4

    neverDisable = False

    InterpolateList = set()
    TeleportList = []

    def __init__(self):
        BaseDistributedObject.__init__(self)
        #self.interpGroup = CInterpolatedGroup()
        self.isOwner = False
        self.interpVars = []
        self.lastInterpolationTime = 0.0
        self.predictable = False

    @staticmethod
    def interpolateObjects():
        #print("interpolate at", globalClock.getFrameTime())
        ctx = InterpolationContext()
        ctx.enableExtrapolation(False)
        ctx.setLastTimestamp(base.cr.lastServerTickTime)
        for do in set(DistributedObject.InterpolateList):
            do.interpolate(globalClock.getFrameTime())
            do.postInterpolate()

    def getInterpolatedVarEntry(self, var):
        for ent in self.interpVars:
            if ent.var == var:
                return ent
        return None

    def addInterpolatedVar(self, var, getter, setter,
                           flags = SimulationVar,
                           arrayIndex = -1):
        if self.getInterpolatedVarEntry(var) is not None:
            # Already added.
            return

        now = globalClock.frame_time

        var.setInterpolationAmount(self.getInterpolateAmount())
        if isinstance(var, InterpolatedFloat):
            default = 0.0
        elif isinstance(var, InterpolatedVec3):
            default = Vec3()
        elif isinstance(var, InterpolatedQuat):
            default = Quat()
        elif isinstance(var, InterpolatedVec2):
            default = Vec2()
        elif isinstance(var, InterpolatedVec4):
            default = Vec4()
        var.reset(default)
        var.recordLastNetworkedValue(default, now)

        self.interpVars.append(InterpVarEntry(var, getter, setter, flags, arrayIndex))

    def removeInterpolatedVar(self, var):
        entry = None
        for ent in self.interpVars:
            if ent.var == var:
                entry = ent
                break
        if entry is not None:
            self.interpVars.remove(entry)

    def updateInterpolationAmount(self):
        for entry in self.interpVars:
            entry.var.setInterpolationAmount(self.getInterpolateAmount())

    #def shouldInterpolate(self):
    #    return True

    def preDataUpdate(self):
        """
        Override this method to do stuff before a state snapshot is unpacked
        onto the object.
        """

        # Restore all of our interpolated variables to the most recently
        # networked value.  This way if the value does not change in the new
        # snapshot, we record the networked value, and not the most recently
        # interpolated value.  However, we only want to do this if the object
        # is actually generated and we have a previously received networked
        # value.
        if self.isDOAlive():
            for entry in self.interpVars:
                if entry.arrayIndex != -1:
                    entry.setter(entry.arrayIndex, entry.var.getLastNetworkedValue())
                else:
                    entry.setter(entry.var.getLastNetworkedValue())

    def getInterpolateAmount(self):
        if self.predictable:
            return 0.0
        serverTickMultiple = 1
        return base.ticksToTime(base.timeToTicks(getClientInterpAmount()) + serverTickMultiple)

    def resetInterpolatedVars(self):
        """
        Resets all interpolated variables to the current values stored on the
        object.
        """
        for entry in self.interpVars:
            if entry.arrayIndex != -1:
                entry.var.reset(entry.getter(entry.arrayIndex))
            else:
                entry.var.reset(entry.getter())

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

        updateLastNetworked = not (flags & self.OmitUpdateLastNetworked)

        for entry in self.interpVars:
            if not (entry.flags & flags):
                continue

            if entry.flags & self.ExcludeAutoLatch:
                continue

            if entry.arrayIndex != -1:
                val = entry.getter(entry.arrayIndex)
            else:
                val = entry.getter()
            if entry.var.recordValue(val, changeTime, updateLastNetworked):
                # Value is changed, we need to interpolate it.
                entry.needsInterpolation = True

        #if self.shouldInterpolate():
            #self.addToInterpolationList()
        DistributedObject.InterpolateList.add(self)

    def onStoreLastNetworkedValue(self):
        for entry in self.interpVars:
            if entry.flags & self.ExcludeAutoLatch:
                continue

            if entry.arrayIndex != -1:
                val = entry.getter(entry.arrayIndex)
            else:
                val = entry.getter()
            entry.var.recordLastNetworkedValue(val, base.frameTime)

    def interpolate(self, now):

        if self.predictable:
            # Fix up time for interpolating prediction results.
            now = base.localAvatar.finalPredictedTick * base.intervalPerTick
            now -= base.intervalPerTick
            now += base.remainder

        done = True
        if now < self.lastInterpolationTime:
            for entry in self.interpVars:
                entry.needsInterpolation = True

        self.lastInterpolationTime = now

        for entry in self.interpVars:
            if not entry.needsInterpolation:
                continue

            if entry.flags & self.ExcludeAutoInterpolate:
                continue

            ret = entry.var.interpolate(now)
            if ret == 1:
                entry.needsInterpolation = False
            else:
                done = False

            if ret != -1:
                if entry.arrayIndex != -1:
                    entry.setter(entry.arrayIndex, entry.var.getInterpolatedValue())
                else:
                    entry.setter(entry.var.getInterpolatedValue())

        if done:
            DistributedObject.InterpolateList.remove(self)

    def addToInterpolationList(self):
        DistributedObject.InterpolateList.add(self)

    def removeFromInterpolationList(self):
        DistributedObject.InterpolateList.discard(self)

    def postDataUpdate(self):
        """
        Override this method to do stuff after a state snapshot has been
        unpacked onto the object.
        """

        if not self.interpVars:
            return

        if not self.predictable:
            self.onLatchInterpolatedVars(
                base.frameTime,
                DistributedObject.SimulationVar)
        else:
            self.onStoreLastNetworkedValue()

    def sendUpdate(self, name, args = []):
        """
        Sends a non-stateful event message from one object view to another.
        """
        base.cl.sendUpdate(self, name, args)

    def announceGenerate(self):
        """ Called when the object is coming into existence *after* the
        baseline state has been applied, or when the object was disabled and
        it is coming back. """

        self.doState = DOState.Alive

    def disable(self):
        """ Called when the object is being temporarily removed/cached away.
        only clean up logical things and remove it from the scene graph, but
        don't tear anything down, because it might come back later via
        announceGenerate(). """

        self.removeFromInterpolationList()
        self.ignoreAll()
        self.removeAllTasks()

        self.doState = DOState.Disabled

    def delete(self):
        self.interpVars = None
        BaseDistributedObject.delete(self)
