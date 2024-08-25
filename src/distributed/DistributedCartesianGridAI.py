from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.task import Task
from direct.task.TaskManagerGlobal import taskMgr
from .DistributedNodeAI import DistributedNodeAI
from .CartesianGridBase import CartesianGridBase
from .GridChild import GridChild

class DistributedCartesianGridAI(DistributedNodeAI, CartesianGridBase):
    notify = directNotify.newCategory("DistributedCartesianGridAI")

    def __init__(self, air, startingZone, gridSize, gridRadius, cellWidth, style="Cartesian"):
        DistributedNodeAI.__init__(self, air)
        CartesianGridBase.__init__(self, startingZone, gridSize, gridRadius, cellWidth, style, 1)

    def delete(self):
        DistributedNodeAI.delete(self)
        CartesianGridBase.disable(self)

    def isGrid(self):
        return CartesianGridBase.isGrid(self)

    def handleChildArrive(self, child, zoneId):
        DistributedNodeAI.handleChildArrive(self, child, zoneId)
        CartesianGridBase.handleChildArrive(self, child, zoneId)

    def handleChildLeave(self, child, zoneId):
        DistributedNodeAI.handleChildLeave(self, child, zoneId)
        CartesianGridBase.handleChildLeave(self, child, zoneId)
        pass
