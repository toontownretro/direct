from panda3d.core import Point3, Vec3, ClipPlaneAttrib, NodePath, PlaneNode, \
    LPlane, RenderState, ColorAttrib, Vec4, TransparencyAttrib, CullFaceAttrib, \
    CullBinAttrib, CardMaker, LineSegs

from .BaseTool import BaseTool
from .ToolOptions import ToolOptions
from direct.foundry.Polygon import Polygon
from direct.foundry.GeomView import GeomView
from direct.foundry.ViewportType import VIEWPORT_3D_MASK, VIEWPORT_2D_MASK
from direct.foundry.Clip import Clip
from direct.foundry.Plane import Plane
from direct.foundry import LEGlobals
from direct.foundry.IDGenerator import IDGenerator
from direct.foundry.KeyBind import KeyBind
from direct.foundry import KeyBinds

from PyQt5 import QtWidgets

from enum import IntEnum

HandleSize = 1

class ClipState(IntEnum):
    Off = 0
    Drawing = 1
    Drawn = 2
    MovingPoint1 = 3
    MovingPoint2 = 4
    MovingPoint3 = 5

class ClipSide(IntEnum):
    Both = 0
    Front = 1
    Back = 2

PlaneVis3DState = RenderState.make(
    ColorAttrib.makeFlat(Vec4(0, 1, 1, 0.5)),
    TransparencyAttrib.make(TransparencyAttrib.MAlpha),
    CullFaceAttrib.make(CullFaceAttrib.MCullNone)
)

PlaneVis2DState = RenderState.make(
    ColorAttrib.makeFlat(Vec4(0, 1, 1, 1)),
    CullBinAttrib.make("fixed", LEGlobals.BoxSort),
    CullFaceAttrib.make(CullFaceAttrib.MCullNone)
)

# Draws the clip plane lines and move handles in each 2D viewport
class ClipToolViewport2D:

    def __init__(self, tool, vp):
        self.tool = tool
        self.vp = vp

        self.hPoint1 = self.makeHandle()
        self.hPoint2 = self.makeHandle()
        self.hPoint3 = self.makeHandle()

    def cleanup(self):
        self.tool  = None
        self.vp = None
        self.hPoint1.removeNode()
        self.hPoint1 = None
        self.hPoint2.removeNode()
        self.hPoint2 = None
        self.hPoint3.removeNode()
        self.hPoint3 = None

    def enable(self):
        self.hPoint1.reparentTo(self.tool.doc.render)
        self.hPoint2.reparentTo(self.tool.doc.render)
        self.hPoint3.reparentTo(self.tool.doc.render)

    def disable(self):
        self.hPoint1.reparentTo(NodePath())
        self.hPoint2.reparentTo(NodePath())
        self.hPoint3.reparentTo(NodePath())

    def update(self):
        scale = HandleSize / self.vp.zoom
        self.hPoint1.setScale(scale)
        self.hPoint2.setScale(scale)
        self.hPoint3.setScale(scale)
        if self.tool.point1:
            self.hPoint1.setPos(self.tool.point1)
        if self.tool.point2:
            self.hPoint2.setPos(self.tool.point2)
        if self.tool.point3:
            self.hPoint3.setPos(self.tool.point3)

    def makeHandle(self):
        cm = CardMaker('handle')
        cm.setFrame(-1, 1, -1, 1)
        np = NodePath(cm.generate())
        np.setLightOff(1)
        np.setFogOff(1)
        np.setBin("fixed", LEGlobals.WidgetSort)
        np.setDepthWrite(False)
        np.setDepthTest(False)
        np.setHpr(self.vp.getViewHpr())
        np.hide(~self.vp.getViewportMask())
        return np

class ClipToolOptions(ToolOptions):

    GlobalPtr = None

    @staticmethod
    def getGlobalPtr():
        if not ClipToolOptions.GlobalPtr:
            ClipToolOptions.GlobalPtr = ClipToolOptions()
        return ClipToolOptions.GlobalPtr

    def __init__(self):
        ToolOptions.__init__(self)

        group = QtWidgets.QGroupBox("Keep Side", self)
        group.setLayout(QtWidgets.QHBoxLayout())

        frontBtn = QtWidgets.QRadioButton("Front", group)
        frontBtn.clicked.connect(self.__toggleFront)
        self.frontBtn = frontBtn
        group.layout().addWidget(frontBtn)

        backBtn = QtWidgets.QRadioButton("Back", group)
        backBtn.clicked.connect(self.__toggleBack)
        self.backBtn = backBtn
        group.layout().addWidget(backBtn)

        bothBtn = QtWidgets.QRadioButton("Both", group)
        bothBtn.clicked.connect(self.__toggleBoth)
        self.bothBtn = bothBtn
        group.layout().addWidget(bothBtn)

        self.layout().addWidget(group)

    def __toggleFront(self):
        self.tool.updateClipSide(ClipSide.Front)

    def __toggleBack(self):
        self.tool.updateClipSide(ClipSide.Back)

    def __toggleBoth(self):
        self.tool.updateClipSide(ClipSide.Both)

    def setTool(self, tool):
        ToolOptions.setTool(self, tool)
        self.updateButtonStates()

    def updateButtonStates(self):
        self.frontBtn.setChecked(False)
        self.backBtn.setChecked(False)
        self.bothBtn.setChecked(False)

        if self.tool.side == ClipSide.Front:
            self.frontBtn.setChecked(True)
        elif self.tool.side == ClipSide.Back:
            self.backBtn.setChecked(True)
        elif self.tool.side == ClipSide.Both:
            self.bothBtn.setChecked(True)

class ClipTool(BaseTool):

    Name = "Clip"
    Icon = "icons/editor-slice.png"
    KeyBind = KeyBind.ClipTool
    ToolTip = "Clip Tool"

    def __init__(self, mgr):
        # For this node, we will instance the objects we are slicing to this node
        # then apply a ClipPlaneAttrib to the node with the plane that the user
        # defined

        BaseTool.__init__(self, mgr)

        # (Original solid, front, back)
        self.tempSolids = []
        self.lines2D = None

        self.vp2Ds = []
        for vp in self.doc.viewportMgr.viewports:
            if vp.is2D():
                self.vp2Ds.append(ClipToolViewport2D(self, vp))

        self.reset()

        self.options = ClipToolOptions.getGlobalPtr()

    def cleanup(self):
        self.clearClipPlane()
        self.tempSolids = None
        if self.lines2D:
            self.lines2D.removeNode()
            self.lines2D = None
        for vp in self.vp2Ds:
            vp.cleanup()
        self.vp2Ds = None
        BaseTool.cleanup(self)

    def enable2DPoints(self):
        for vp in self.vp2Ds:
            vp.enable()

    def update2DPoints(self):
        for vp in self.vp2Ds:
            vp.update()

    def disable2DPoints(self):
        for vp in self.vp2Ds:
            vp.disable()

    def disable2DLines(self):
        if self.lines2D:
            self.lines2D.removeNode()
            self.lines2D = None

    def update2DLines(self):
        self.disable2DLines()
        segs = LineSegs()
        segs.setColor((0, 1, 1, 1))
        segs.moveTo(self.point1)
        segs.drawTo(self.point2)
        segs.moveTo(self.point2)
        segs.drawTo(self.point3)
        segs.moveTo(self.point3)
        segs.drawTo(self.point1)
        self.lines2D = self.doc.render.attachNewNode(segs.create())
        self.lines2D.setBin("fixed", LEGlobals.BoxSort)
        self.lines2D.setDepthWrite(False)
        self.lines2D.setDepthTest(False)
        self.lines2D.hide(~VIEWPORT_2D_MASK)

    def reset(self):
        self.point1 = None
        self.point2 = None
        self.point3 = None
        self.drawingPoint = None
        self.controlIsDown = False
        self.prevState = ClipState.Off
        self.state = ClipState.Off
        self.side = ClipSide.Front
        self.clearClipPlane()
        self.disable2DPoints()
        self.disable2DLines()
        self.doc.updateAllViews()

    def activate(self):
        BaseTool.activate(self)
        self.accept('mouse1', self.mouseDown)
        self.accept('mouse1-up', self.mouseUp)
        self.accept('mouseMoved', self.mouseMoved)
        self.accept('control', self.controlDown)
        self.accept(KeyBinds.getPandaShortcut(KeyBind.Confirm), self.confirmClip)
        self.accept(KeyBinds.getPandaShortcut(KeyBind.Cancel), self.doResetKeepSide)

    def toolTriggered(self):
        self.cycleClipSide()
        self.options.updateButtonStates()

    def doResetKeepSide(self):
        side = ClipSide(self.side)
        self.reset()
        self.side = side

    def cycleClipSide(self):
        self.updateClipSide((self.side + 1) % 3)
        self.doc.updateAllViews()

    def confirmClip(self):
        if self.point1 is None or self.point2 is None or self.point3 is None:
            self.reset()
            return

        clipPlane = Plane.fromVertices(self.point1, self.point2, self.point3)
        side = ClipSide(self.side)
        self.reset()
        solids = []
        for obj in base.selectionMgr.selectedObjects:
            if obj.ObjectName == "solid":
                solids.append(obj)
        base.actionMgr.performAction("Clip %i solid(s)" % len(solids), Clip(solids, clipPlane, side != ClipSide.Back, side != ClipSide.Front))
        self.side = side

    def controlDown(self):
        self.controlIsDown = True

    def controlUp(self):
        self.controlIsDown = False

    def disable(self):
        self.reset()
        BaseTool.disable(self)

    def getStateAtPoint(self, mouse, viewport):
        if self.point1 is None or self.point2 is None or self.point3 is None:
            return ClipState.Off

        p = viewport.viewportToWorld(mouse)
        p1 = viewport.flatten(self.point1)
        p2 = viewport.flatten(self.point2)
        p3 = viewport.flatten(self.point3)

        d = HandleSize / viewport.zoom

        if (p.x >= p1.x - d and p.x <= p1.x + d and p.z >= p1.z - d and p.z <= p1.z + d):
            return ClipState.MovingPoint1
        if (p.x >= p2.x - d and p.x <= p2.x + d and p.z >= p2.z - d and p.z <= p2.z + d):
            return ClipState.MovingPoint2
        if (p.x >= p3.x - d and p.x <= p3.x + d and p.z >= p3.z - d and p.z <= p3.z + d):
            return ClipState.MovingPoint3

        return ClipState.Off

    def mouseDown(self):
        vp = base.viewportMgr.activeViewport
        if not vp or not vp.is2D():
            return

        self.prevState = self.state
        mouse = vp.getMouse()
        point = base.snapToGrid(vp.expand(vp.viewportToWorld(mouse)))
        st = self.getStateAtPoint(mouse, vp)
        if self.state == ClipState.Off or st == ClipState.Off:
            self.state = ClipState.Drawing
            self.drawingPoint = point
        elif self.state == ClipState.Drawn:
            self.state = st

    def mouseMoved(self, vp):
        if not vp.is2D():
            return

        point1 = self.point1
        point2 = self.point2
        point3 = self.point3

        mouse = vp.getMouse()
        point = base.snapToGrid(vp.viewportToWorld(mouse, False))
        st = self.getStateAtPoint(mouse, vp)
        if self.state == ClipState.Drawing:
            self.state = ClipState.MovingPoint2
            point1 = self.drawingPoint
            point2 = point
            point3 = point1 + base.snapToGrid(vp.getUnusedCoordinate(Vec3(128)))
            self.enable2DPoints()
        elif self.state == ClipState.MovingPoint1:
            # Move point 1
            cp1 = vp.getUnusedCoordinate(point1) + point
            if self.controlIsDown:
                diff = self.point1 - cp1
                point2 -= diff
                point3 -= diff
            point1 = cp1
        elif self.state == ClipState.MovingPoint2:
            # Move point 2
            cp2 = vp.getUnusedCoordinate(point2) + point
            if self.controlIsDown:
                diff = point2 - cp2
                point1 -= diff
                point3 -= diff
            point2 = cp2
        elif self.state == ClipState.MovingPoint3:
            # Move point 3
            cp3 = vp.getUnusedCoordinate(point3) + point
            if self.controlIsDown:
                diff = point3 - cp3
                point1 -= diff
                point2 -= diff
            point3 = cp3

        if point1 != self.point1 or point2 != self.point2 or point3 != self.point3:
            self.point1 = point1
            self.point2 = point2
            self.point3 = point3
            self.update2DLines()
            self.update2DPoints()
            self.updateClipPlane()
            self.doc.updateAllViews()

    def clearClipPlane(self):
        for origSolid, front, back in self.tempSolids:
            front.delete()
            back.delete()
            # Reshow the original solid
            origSolid.np.unstash()
        self.tempSolids = []

    def updateClipPlane(self):
        self.clearClipPlane()

        if self.point1 == self.point2 or self.point1 == self.point3 or self.point2 == self.point3:
            return
        plane = Plane.fromVertices(self.point1, self.point2, self.point3)
        tempGen = IDGenerator()

        for obj in base.selectionMgr.selectedObjects:
            if obj.ObjectName != "solid":
                continue
            ret, back, front = obj.split(plane, tempGen, True)
            if ret:
                front.np.reparentTo(self.doc.render)
                back.np.reparentTo(self.doc.render)
                self.tempSolids.append((obj, front, back))
                # Hide the original solid
                obj.np.stash()

        self.updateClipSide(self.side)

    def updateClipSide(self, side):
        self.side = side

        for _, front, back in self.tempSolids:
            if self.side == ClipSide.Both:
                front.showBoundingBox()
                front.showClipVisKeep()
                back.showBoundingBox()
                back.showClipVisKeep()
            elif self.side == ClipSide.Front:
                front.showClipVisKeep()
                front.hideBoundingBox()
                back.showClipVisRemove()
                back.showBoundingBox()
            elif self.side == ClipSide.Back:
                front.showClipVisRemove()
                front.showBoundingBox()
                back.showClipVisKeep()
                back.hideBoundingBox()

    def mouseUp(self):
        vp = base.viewportMgr.activeViewport
        if not vp or not vp.is2D():
            return

        point = base.snapToGrid(vp.expand(vp.viewportToWorld(vp.getMouse())))
        if self.state == ClipState.Drawing:
            # Do nothing
            self.state = self.prevState
        else:
            self.state = ClipState.Drawn

    def update(self):
        self.update2DPoints()
