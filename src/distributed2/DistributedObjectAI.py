from .BaseDistributedObject import BaseDistributedObject

# Base server network object
class DistributedObjectAI(BaseDistributedObject):

    def __init__(self):
        BaseDistributedObject.__init__(self)
        self.owner = None

    def simulate(self):
        BaseDistributedObject.simulate(self)
        self.simulationTime = globalClock.getFrameTime()

    def SendProxy_simulationTime(self):
        tickNumber = base.timeToTicks(self.simulationTime)
        # tickBase is current tick rounded down to closest 100 ticks
        tickBase = base.getNetworkBase(base.tickCount, self.doId)
        addT = 0
        if tickNumber >= tickBase:
            addT = (tickNumber - tickBase) & 0xFF

        return addT

    def sendUpdate(self, name, args = [], client = None):
        """
        Sends a non-stateful event message from one object view to another.
        If client is not None, sends the message to that client's object view.
        """
        base.sv.sendUpdate(self, name, args, client)

    def delete(self):
        self.owner = None
        BaseDistributedObject.delete(self)
