"""DistributedNode module: contains the DistributedNode class"""

from panda3d.core import NodePath
from . import DistributedObject


class DistributedNode(DistributedObject.DistributedObject, NodePath):
    """Distributed Node class:"""

    def __init__(self, cr):
        if not hasattr(self, 'DistributedNode_initialized'):
            self.DistributedNode_initialized = 1
            self.gotStringParentToken = 0
            DistributedObject.DistributedObject.__init__(self, cr)
            if not self.this:
                NodePath.__init__(self, "DistributedNode")

    def disable(self):
        if self.activeState != DistributedObject.ESDisabled:
            if not self.isEmpty():
                self.reparentTo(hidden)
            DistributedObject.DistributedObject.disable(self)

    def delete(self):
        if not hasattr(self, 'DistributedNode_deleted'):
            self.DistributedNode_deleted = 1
            if not self.isEmpty():
                self.removeNode()
            DistributedObject.DistributedObject.delete(self)

    def generate(self):
        DistributedObject.DistributedObject.generate(self)
        self.gotStringParentToken = 0

    def __cmp__(self, other):
        # DistributedNode inherits from NodePath, which inherits a
        # definition of __cmp__ from FFIExternalObject that uses the
        # NodePath's compareTo() method to compare different
        # NodePaths.  But we don't want this behavior for
        # DistributedNodes; DistributedNodes should only be compared
        # pointerwise.
        if self is other:
            return 0
        else:
            return 1

    ### setParent ###

    def b_setParent(self, parentToken):
        if isinstance(parentToken, str):
            self.setParentStr(parentToken)
        else:
            self.setParent(parentToken)
        # it's important to call the local setParent first.
        self.d_setParent(parentToken)

    def d_setParent(self, parentToken):
        if isinstance(parentToken, str):
            self.sendUpdate("setParentStr", [parentToken])
        else:
            self.sendUpdate("setParent", [parentToken])

    def setParentStr(self, parentTokenStr):
        assert self.notify.debug('setParentStr: %s' % parentTokenStr)
        assert self.notify.debug('isGenerated: %s' % self.isGenerated())
        if len(parentTokenStr) > 0:
            self.do_setParent(parentTokenStr)
            self.gotStringParentToken = 1

    def setParent(self, parentToken):
        assert self.notify.debug('setParent: %s' % parentToken)
        assert self.notify.debug('isGenerated: %s' % self.isGenerated())
        # if we are not yet generated and we just got a parent token
        # as a string, ignore whatever value comes in here
        justGotRequiredParentAsStr = ((not self.isGenerated()) and
                                      self.gotStringParentToken)
        if not justGotRequiredParentAsStr:
            if parentToken != 0:
                self.do_setParent(parentToken)
        self.gotStringParentToken = 0

    def do_setParent(self, parentToken):
        """do_setParent(self, int parentToken)

        This function is defined simply to allow a derived class (like
        DistributedAvatar) to override the behavior of setParent if
        desired.
        """
        if not self.isDisabled():
            self.cr.parentMgr.requestReparent(self, parentToken)

    ###### set pos and hpr functions #######

    # setX provided by NodePath
    def d_setX(self, x):
        self.sendUpdate("setX", [x])

    # setY provided by NodePath
    def d_setY(self, y):
        self.sendUpdate("setY", [y])

    # setZ provided by NodePath
    def d_setZ(self, z):
        self.sendUpdate("setZ", [z])

    # setH provided by NodePath
    def d_setH(self, h):
        self.sendUpdate("setH", [h])

    # setP provided by NodePath
    def d_setP(self, p):
        self.sendUpdate("setP", [p])

    # setR provided by NodePath
    def d_setR(self, r):
        self.sendUpdate("setR", [r])

    def setXY(self, x, y):
        self.setX(x)
        self.setY(y)
    def d_setXY(self, x, y):
        self.sendUpdate("setXY", [x, y])

    def setXZ(self, x, z):
        self.setX(x)
        self.setZ(z)
    def d_setXZ(self, x, z):
        self.sendUpdate("setXZ", [x, z])

    # setPos provided by NodePath
    def d_setPos(self, x, y, z):
        self.sendUpdate("setPos", [x, y, z])

    # setHpr provided by NodePath
    def d_setHpr(self, h, p, r):
        self.sendUpdate("setHpr", [h, p, r])

    def setXYH(self, x, y, h):
        self.setX(x)
        self.setY(y)
        self.setH(h)
    def d_setXYH(self, x, y, h):
        self.sendUpdate("setXYH", [x, y, h])

    def setXYZH(self, x, y, z, h):
        self.setPos(x, y, z)
        self.setH(h)
    def d_setXYZH(self, x, y, z, h):
        self.sendUpdate("setXYZH", [x, y, z, h])

    # setPosHpr provided by NodePath
    def d_setPosHpr(self, x, y, z, h, p, r):
        self.sendUpdate("setPosHpr", [x, y, z, h, p, r])
