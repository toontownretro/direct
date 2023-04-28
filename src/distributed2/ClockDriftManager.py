from panda3d.core import *

cl_clock_correction = ConfigVariableBool("cl-clock-correction", True)
cl_clockdrift_max_ms = ConfigVariableInt("cl-clock-drift-max-ms", 150)
cl_clock_show_debug_info = ConfigVariableBool("cl-clock-show-debug-info", False)
cl_clock_correction_force_server_tick = ConfigVariableInt("cl-clock-correction-force-server-tick", 999)
cl_clock_correction_adjustment_max_amount = ConfigVariableInt("cl-clock-correction-adjustment-max-amount", 200)
cl_clock_correction_adjustment_min_offset = ConfigVariableInt("cl-clock-correction-adjustment-min-offset", 10)
cl_clock_correction_adjustment_max_offset = ConfigVariableInt("cl-clock-correction-adjustment-max-offset", 90)

class ClockDriftManager:

    def __init__(self):
        self.clear()

    def remapVal(self, val, A, B, C, D):
        if A == B:
            return D if val >= B else C

        return C + (D - C) * (val - A) / (B - A)

    def getCurrentClockDifference(self):
        total = 0.0
        for i in range(16):
            total += self.clockOffsets[i]
        return total / 16

    def getClockAdjustmentAmount(self, currDiffInMS):
        # Clamp to the min/max offsets.
        currDiffInMS = max(cl_clock_correction_adjustment_min_offset.getValue(),
          min(cl_clock_correction_adjustment_max_offset.getValue(), currDiffInMS))

        returnValue = self.remapVal(currDiffInMS,
          cl_clock_correction_adjustment_min_offset.getValue(),
          cl_clock_correction_adjustment_max_offset.getValue(),
          0,
          cl_clock_correction_adjustment_max_amount.getValue() / 1000.0)

        return returnValue

    def setServerTick(self, tick):
        base.clockMgr.setRestoreTickCount(False)

        self.serverTick = tick
        maxDriftTicks = base.timeToTicks(cl_clockdrift_max_ms.getValue() / 1000.0)

        clientTick = base.tickCount + base.currentTicksThisFrame - 1
        if cl_clock_correction_force_server_tick.getValue() == 999:
            if (not self.isClockCorrectionEnabled()) or (clientTick == 0) or (abs(tick - clientTick) > maxDriftTicks):
                base.tickCount = tick - (base.currentTicksThisFrame - 1)
                if base.tickCount < base.oldTickCount:
                    base.oldTickCount = base.tickCount
                self.clockOffsets = [0] * 16
        else:
            # Used for testing.
            base.tickCount = tick + cl_clock_correction_force_server_tick.getValue()

        # Adjust the clock offset
        self.clockOffsets[self.currentClockOffset] = clientTick - self.serverTick
        self.currentClockOffset = (self.currentClockOffset + 1) % 16

    def adjustFrameTime(self, inputFrameTime):
        adjustmentThisFrame = 0
        adjustmentPerSec = 0
        if self.isClockCorrectionEnabled():
            # Get the clock difference in seconds.
            currDiffInSeconds = self.getCurrentClockDifference() * base.intervalPerTick
            currDiffInMS = currDiffInSeconds * 1000.0

            # Is the server ahead or behind us?
            if currDiffInMS > cl_clock_correction_adjustment_min_offset.getValue():
                adjustmentPerSec = -self.getClockAdjustmentAmount(currDiffInMS)
                adjustmentThisFrame = inputFrameTime * adjustmentPerSec
                adjustmentThisFrame = max(adjustmentThisFrame, -currDiffInSeconds)
            elif currDiffInMS < -cl_clock_correction_adjustment_min_offset.getValue():
                adjustmentPerSec = self.getClockAdjustmentAmount(-currDiffInMS)
                adjustmentThisFrame = inputFrameTime * adjustmentPerSec
                adjustmentThisFrame = min(adjustmentThisFrame, -currDiffInSeconds)

            self.adjustAverageDifferenceBy(adjustmentThisFrame)

        self.showDebugInfo(adjustmentPerSec)
        return inputFrameTime + adjustmentThisFrame

    def showDebugInfo(self, adjustment):
        if not cl_clock_show_debug_info.getValue():
            return

        if self.isClockCorrectionEnabled():
            high = -999
            low = 999
            exactDiff = base.tickCount - self.serverTick
            for i in range(16):
                high = max(high, self.clockOffsets[i])
                low = min(low, self.clockOffsets[i])
            print("Clock drift: adjustment (per sec): %.2fms, avg: %.3f, lo: %d, hi: %d, ex: %d"
                  % (adjustment * 1000.0, self.getCurrentClockDifference(), low, high, exactDiff))
        else:
            print("Clock drift disabled.")

    def adjustAverageDifferenceBy(self, amountInSeconds):
        # Don't adjust the average if it's already tiny.
        c = self.getCurrentClockDifference()
        if c < 0.05:
            return

        amountInTicks = amountInSeconds / base.intervalPerTick
        factor = 1 + amountInTicks / c

        for i in range(16):
            self.clockOffsets[i] *= factor

    def isClockCorrectionEnabled(self):
        return cl_clock_correction.getValue() and base.cr.connected and (base.cr.serverTickCount != -1)

    def clear(self):
        self.clockOffsets = [0] * 16
        self.currentClockOffset = 0
        self.serverTick = 0 # Last-received tick from the server.
        self.clientTick = 0 # Client's own tick counter (specifically, for interpolation during rendering).
                            # The server may be on a slightly different tick and the client will drift towards it.
