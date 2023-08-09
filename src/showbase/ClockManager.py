"""ClockManager module: contains the ClockManager class."""

from panda3d.core import ClockObject

import sys

# Network time - simulation time on server
# Client time - local client time since game started, incremented each epoch
# Client network time - simulation time in client space (network time + client time delta)

class ClockManager:

    def __init__(self, clock):
        self.clock = clock
        self.savedStack = []
        self.simulationDepth = 0
        self.simulationDelta = 0.0
        self.simulationDeltaNoRemainder = 0.0

    def setSimulationDelta(self, delta):
        self.simulationDelta = delta

    def calcSimulationDelta(self, tick):
        self.simulationDelta = self.getClientFrameTime() - ((tick * base.intervalPerTick) + base.remainder)
        self.simulationDeltaNoRemainder = self.getClientFrameTime() - (tick * base.intervalPerTick)

    def isInSimulationClock(self):
        return self.simulationDepth > 0

    def getNetworkTime(self):
        if self.isInSimulationClock():
            return self.clock.frame_time - self.simulationDelta
        else:
            return base.tickCount * base.intervalPerTick

    def getClientSimulationTime(self):
        if self.isInSimulationClock():
            return self.clock.frame_time
        else:
            return self.getNetworkTime() + self.simulationDelta

    def getClientFrameTime(self):
        if self.isInSimulationClock():
            return self.savedStack[0][1]
        else:
            return self.clock.frame_time

    def networkToClientTime(self, networkTime):
        return networkTime + self.simulationDelta

    def clientToNetworkTime(self, clientTime):
        return clientTime - self.simulationDelta

    def getTime(self):
        # Context-aware time retrieval.
        if IS_CLIENT and self.isInSimulationClock() and base.cr.prediction.inPrediction:
            #if IS_CLIENT and base.cr.prediction.inPrediction:
            # If we're in prediction, assume we want to get the
            # network space time, rather than the client-space
            # network time.  We probably want to store some difference
            # in time as a prediction result, which must match the
            # server network time.
            return self.clock.frame_time - self.simulationDelta
        else:
            return self.clock.frame_time
            #else:
            #    return self.getClientSimulationTime()
        #else:
        #    return self.getClientFrameTime()

    def getClientTime(self):
        return self.clock.frame_time

    def getDeltaTime(self):
        return self.clock.dt
        #if self.isInSimulationClock():
        #    return base.intervalPerTick
        #else:
        #    return self.clock.getDt()

    def setRestoreTickCount(self, val):
        if self.savedStack:
            self.savedStack[len(self.savedStack) - 1][5] = val

    def enterSimulationTime(self, tickNumber, timeTick=None, dt=None):
        if timeTick is None:
            timeTick = tickNumber
        if dt is None:
            dt = base.intervalPerTick
        self.restoreTickCount = True
        self.savedStack.append([base.tickCount, self.clock.frame_time, self.clock.dt, self.clock.frame_count, self.clock.mode, True])
        base.tickCount = tickNumber
        self.clock.mode = ClockObject.MSlave
        self.clock.frame_time = (timeTick * base.intervalPerTick) + self.simulationDelta
        self.clock.dt = dt
        self.clock.frame_count = base.tickCount
        self.simulationDepth += 1

    def exitSimulationTime(self):
        assert self.simulationDepth
        tickCount, frameTime, dt, frameCount, mode, restoreTickCount = self.savedStack.pop()
        if restoreTickCount:
            base.tickCount = tickCount
        self.clock.mode = ClockObject.MSlave
        self.clock.frame_time = frameTime
        self.clock.dt = dt
        self.clock.frame_count = frameCount
        self.clock.mode = mode
        self.simulationDepth -= 1
