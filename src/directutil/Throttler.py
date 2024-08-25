import sys

# class that can throttle throughput based on a size, time, and throughput
class Throttler:
    def __init__(self, enabled):
        # throttling enabled
        self.enabled = enabled
        # last data amount recorded
        self.suspiciousEventDataTime = sys.maxsize
        # last calculated data size
        self.suspiciousEventDataSize = 0
        # how fast throttleer allows data through
        self.decay = 0
        # when send status changes, call this
        self.callback = None
        # current send status
        self.canSend = True

    #--------------------------------------------------------------------------
    # Function:   enable throttling, otherwise there is no limiting
    # Parameters: enable, wether throttling should be enabled
    # Changes:    self.enabled
    # Returns:    nothing
    #--------------------------------------------------------------------------
    def enable(self, enable):
        self.enabled = enable
        
    #--------------------------------------------------------------------------
    # Function:   cleanup throttling
    # Parameters: none
    # Changes:    self.enabled, taskMgr
    # Returns:    nothing
    #--------------------------------------------------------------------------
    def cleanup(self):
        self.enabled = False
        taskMgr.remove(id(self) + '-throttler')

    #--------------------------------------------------------------------------
    # Function:   set throughput rate (in size-units/second)
    # Parameters: decay, rate at which the throttler clears up
    # Changes:    self.decay
    # Returns:    nothing
    #--------------------------------------------------------------------------
    def setDecay(self, decay):
        self.decay = float(decay)

    #--------------------------------------------------------------------------
    # Function:   refresh data allowance
    # Parameters: None
    # Changes:    self.suspiciousEventDataSize
    # Returns:    nothing
    #--------------------------------------------------------------------------
    def _recalcResidual(self):
        currTime = globalClock.getFrameTime()
        timePassed = currTime - self.suspiciousEventDataTime
        if timePassed <= 0 or self.suspiciousEventDataSize == 0:
            # no need to recalc
            return
        timeLeft = self.suspiciousEventDataSize / self.decay
        decayRatio = timePassed / timeLeft
        print("suspiciousEventDataSize: %s decayRatio: %s timeLeft: %s timePassed: %s"%(
            self.suspiciousEventDataSize,decayRatio,timeLeft,timePassed))
        self.suspiciousEventDataSize = max(0,self.suspiciousEventDataSize - self.suspiciousEventDataSize * decayRatio)
        self.suspiciousEventDataTime = currTime
        self._updateStatus()

    #--------------------------------------------------------------------------
    # Function:   record new data sent
    # Parameters: amount, number of bytes sent
    # Changes:    self.suspiciousEventDataSize, self.suspiciousEventDataTime
    # Returns:    nothing
    #--------------------------------------------------------------------------
    def recordData(self, amount):
        self._recalcResidual()
        self.suspiciousEventDataSize = self.suspiciousEventDataSize + amount
        self.suspiciousEventDataTime = globalClock.getFrameTime()
        self._updateStatus()

    #--------------------------------------------------------------------------
    # Function:   update status
    # Parameters: none
    # Changes:
    # Returns:
    #--------------------------------------------------------------------------
    def _callbackTask(self, Task=None):
        self._recalcResidual()
        self._updateStatus()
        return Task.again

    #--------------------------------------------------------------------------
    # Function:   send status has changed, send it out to clients
    # Parameters: none
    # Changes:    none
    # Returns:    nothing
    #--------------------------------------------------------------------------
    def _statusChange(self):
        if self.callback:
            self.callback(self.getAllowSend())
            
    #--------------------------------------------------------------------------
    # Function:   see if send status should change
    # Parameters: none
    # Changes:    self.canSend
    # Returns:    nothing
    #--------------------------------------------------------------------------
    def _updateStatus(self):
        oldStatus = self.canSend
        self.canSend = self.suspiciousEventDataSize <= 0
        if oldStatus != self.canSend:
            # status changed, send out notification
            self._statusChange()

    #--------------------------------------------------------------------------
    # Function:   determine if more data can be sent
    # Parameters: none
    # Changes:    self.suspiciousEventDataSize
    # Returns:    True if data can be sent
    #--------------------------------------------------------------------------
    def getAllowSend(self):
        return not self.enabled or self.canSend

    #--------------------------------------------------------------------------
    # Function:   specify a function to be used when status changes
    # Parameters: callback, callback to use when can/can't send changes
    # Changes:    self.callback
    # Returns:    nothing
    #--------------------------------------------------------------------------
    def updateCallback(self, callback):
        self.callback = callback
        if callback:
            taskMgr.doMethodLater(5, self._callbackTask, str(id(self)) + '-throttler')
        else:
            taskMgr.remove(str(id(self)) + '-throttler')
