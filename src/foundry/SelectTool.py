from panda3d.core import RenderState, ColorAttrib, Vec4, Point3, NodePath, CollisionBox, CollisionNode, CollisionTraverser, BitMask32
from panda3d.core import CollisionHandlerQueue, GeomNode

from .BoxTool import BoxTool, ResizeHandle, BoxAction
from direct.foundry import LEGlobals
from direct.foundry import LEUtils
from direct.foundry.ViewportType import VIEWPORT_3D_MASK, VIEWPORT_2D_MASK
from direct.foundry.Select import Select, Deselect
from direct.foundry.KeyBind import KeyBind

from direct.foundry.Box import Box
from direct.foundry.GeomView import GeomView

class SelectTool(BoxTool):

    Name = "Select"
    ToolTip = "Select Tool"
    KeyBind = KeyBind.SelectTool
    Icon = "icons/editor-select.png"
    Draw3DBox = False

    def __init__(self, mgr):
        BoxTool.__init__(self, mgr)
        self.box.setColor(Vec4(1, 1, 0, 1))
        self.suppressSelect = False

    def cleanup(self):
        self.suppressSelect = None
        self.multiSelect = None
        BoxTool.cleanup(self)

    def activate(self):
        BoxTool.activate(self)
        self.accept('shift-mouse1', self.mouseDown)
        self.accept('shift-mouse1-up', self.mouseUp)
        self.accept('wheel_up', self.wheelUp)
        self.accept('wheel_down', self.wheelDown)
        self.accept('shift', self.shiftDown)
        self.accept('shift-up', self.shiftUp)
        self.accept('selectionsChanged', self.selectionChanged)
        self.accept('selectionModeChanged', self.selectionModeChanged)

        base.selectionMgr.selectionMode.toolActivate()

    def deactivate(self):
        BoxTool.deactivate(self)
        base.selectionMgr.selectionMode.toolDeactivate()

    def selectionModeChanged(self, old, mode):
        mode.toolActivate()

    def enable(self):
        BoxTool.enable(self)
        self.multiSelect = False
        self.mouseIsDown = False

    def shiftDown(self):
        self.multiSelect = True

    def shiftUp(self):
        self.multiSelect = False

    def selectionChanged(self):
        pass

    def mouseDown(self):
        vp = base.viewportMgr.activeViewport
        if not vp:
            return

        self.mouseIsDown = True

        BoxTool.mouseDown(self)

        if self.suppressSelect:
            return

        ret = base.selectionMgr.selectionMode.selectObjectUnderMouse(self.multiSelect)
        if (not ret) and (not self.multiSelect) and (self.state.action != BoxAction.ReadyToResize):
            # Deselect all if not doing multi-select and no hits
            self.deselectAll()

    def mouseUp(self):
        self.mouseIsDown = False
        vp = base.viewportMgr.activeViewport
        if not vp:
            return
        if vp.is2D():
            BoxTool.mouseUp(self)

    def boxDrawnConfirm(self):
        invalid, mins, maxs = self.getSelectionBox()
        if invalid:
            return

        base.selectionMgr.selectionMode.selectObjectsInBox(mins, maxs)

    def wheelUp(self):
        if not self.mouseIsDown:
            return

        base.selectionMgr.selectionMode.cycleNextSelection(self.multiSelect)

    def wheelDown(self):
        if not self.mouseIsDown:
            return

        base.selectionMgr.selectionMode.cyclePreviousSelection(self.multiSelect)

    def escapeDown(self):
        BoxTool.escapeDown(self)
        self.deselectAll()

    def deselectAll(self):
        base.selectionMgr.selectionMode.deselectAll()

    def disable(self):
        BoxTool.disable(self)
        self.multiSelect = False
        self.mouseIsDown = False
