from panda3d.core import Point3, NodePath, BitMask32, RenderState, ColorAttrib, Vec4, LightAttrib, FogAttrib, LineSegs
from panda3d.core import Vec3, LPlane, GeomNode

from PyQt5 import QtWidgets, QtCore

from .BaseTool import BaseTool
from .ToolOptions import ToolOptions
from direct.foundry.Box import Box
from direct.foundry.GeomView import GeomView
from direct.foundry.GridSettings import GridSettings
from direct.foundry.Entity import Entity
from direct.foundry import LEUtils, LEGlobals, LEConfig
from direct.foundry.Create import Create
from direct.foundry.Select import Deselect
from direct.foundry.ChangeSelectionMode import ChangeSelectionMode
from direct.foundry.SelectionType import SelectionType
from direct.foundry.Select import Select
from direct.foundry.ActionGroup import ActionGroup
from direct.foundry.KeyBind import KeyBind

import random

VisState = RenderState.make(
    ColorAttrib.makeFlat(Vec4(0, 1, 0, 1)),
    LightAttrib.makeAllOff(),
    FogAttrib.makeOff()
)

class EntityToolOptions(ToolOptions):

    GlobalPtr = None
    @staticmethod
    def getGlobalPtr():
        self = EntityToolOptions
        if not self.GlobalPtr:
            self.GlobalPtr = EntityToolOptions()
        return self.GlobalPtr

    def __init__(self):
        ToolOptions.__init__(self)

        lbl = QtWidgets.QLabel("Entity class")
        self.layout().addWidget(lbl)
        combo = QtWidgets.QComboBox()
        self.layout().addWidget(combo)
        check = QtWidgets.QCheckBox("Random yaw")
        check.stateChanged.connect(self.__randomYawChecked)
        self.layout().addWidget(check)
        self.randomYawCheck = check

        self.combo = combo
        self.combo.currentTextChanged.connect(self.__handleClassChanged)
        self.combo.setEditable(True)

        self.updateEntityClasses()

    def setTool(self, tool):
        ToolOptions.setTool(self, tool)
        self.combo.setCurrentText(self.tool.classname)
        self.randomYawCheck.setChecked(self.tool.applyRandomYaw)

    def __handleClassChanged(self, classname):
        if not self.tool:
            return
        self.tool.classname = classname

    def __randomYawChecked(self, state):
        self.tool.applyRandomYaw = (state == QtCore.Qt.Checked)

    def updateEntityClasses(self):
        self.combo.clear()

        names = []

        for ent in base.fgd.entities:
            if ent.class_type == 'PointClass':
                names.append(ent.name)

        names.sort()

        completer = QtWidgets.QCompleter(names)
        completer.setCompletionMode(QtWidgets.QCompleter.InlineCompletion)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.combo.setCompleter(completer)

        for name in names:
            self.combo.addItem(name)

# Tool used to place an entity in the level.
class EntityTool(BaseTool):

    Name = "Entity"
    ToolTip = "Entity Tool"
    KeyBind = KeyBind.EntityTool
    Icon = "icons/editor-entity.png"

    def __init__(self, mgr):
        BaseTool.__init__(self, mgr)
        self.classname = LEConfig.default_point_entity.getValue()
        self.applyRandomYaw = False
        self.pos = Point3(0, 0, 0)

        self.mouseIsDown = False
        self.hasPlaced = False

        # Maintain a constant visual scale for the box in 2D,
        # but a constant physical scale in 3D.
        self.size2D = 4
        self.size3D = 2

        self.boxSize = 0.5

        # Setup the visualization of where our entity will be placed
        # if we use the 2D viewport.
        self.visRoot = NodePath("entityToolVis")
        self.visRoot.setColor(Vec4(0, 1, 0, 1), 1)
        self.visRoot.setLightOff(1)
        self.visRoot.setFogOff(1)
        self.box = Box()
        for vp in self.doc.viewportMgr.viewports:
            view = self.box.addView(GeomView.Lines, vp.getViewportMask())
            if vp.is2D():
                view.np.setBin("fixed", LEGlobals.BoxSort)
                view.np.setDepthWrite(False)
                view.np.setDepthTest(False)
            else:
                view.np.setScale(self.size3D)
            view.viewport = vp
        self.box.setMinMax(Point3(-self.boxSize), Point3(self.boxSize))
        self.box.np.reparentTo(self.visRoot)
        self.box.generateGeometry()
        lines = LineSegs()
        lines.moveTo(Point3(-10000, 0, 0))
        lines.drawTo(Point3(10000, 0, 0))
        lines.moveTo(Point3(0, -10000, 0))
        lines.drawTo(Point3(0, 10000, 0))
        lines.moveTo(Point3(0, 0, -10000))
        lines.drawTo(Point3(0, 0, 10000))
        self.lines = self.visRoot.attachNewNode(lines.create())

        self.options = EntityToolOptions.getGlobalPtr()

    def cleanup(self):
        self.classname = None
        self.pos = None
        self.mouseIsDown = None
        self.hasPlaced = None
        self.size2D = None
        self.size3D = None
        self.boxSize = None
        self.box.cleanup()
        self.box = None
        self.lines.removeNode()
        self.lines = None
        self.visRoot.removeNode()
        self.visRoot = None
        self.applyRandomYaw = None
        BaseTool.cleanup(self)

    def enable(self):
        BaseTool.enable(self)
        self.reset()

    def activate(self):
        BaseTool.activate(self)
        self.accept('mouse1', self.mouseDown)
        self.accept('mouse1-up', self.mouseUp)
        self.accept('mouseMoved', self.mouseMoved)
        self.accept('enter', self.confirm)
        self.accept('escape', self.reset)
        self.accept('arrow_up', self.moveUp)
        self.accept('arrow_down', self.moveDown)
        self.accept('arrow_left', self.moveLeft)
        self.accept('arrow_right', self.moveRight)

    def disable(self):
        BaseTool.disable(self)
        self.reset()

    def reset(self):
        self.hideVis()
        self.mouseIsDown = False
        self.hasPlaced = False
        self.pos = Point3(0, 0, 0)

    def updatePosFromViewport(self, vp):
        mouse = vp.getMouse()
        pos = base.snapToGrid(vp.viewportToWorld(mouse, flatten = False))
        # Only update the axes used by the viewport
        for axis in vp.spec.flattenIndices:
            self.pos[axis] = pos[axis]

        self.visRoot.setPos(self.pos)

        self.doc.updateAllViews()

    def updatePos(self, pos):
        self.pos = pos
        self.visRoot.setPos(pos)
        self.doc.updateAllViews()

    def hideVis(self):
        self.visRoot.reparentTo(NodePath())
        self.doc.updateAllViews()

    def showVis(self):
        self.visRoot.reparentTo(self.doc.render)
        self.doc.updateAllViews()

    def mouseDown(self):
        vp = base.viewportMgr.activeViewport
        if not vp:
            return

        if vp.is3D():
            # If we clicked in the 3D viewport, try to intersect with an existing MapObject
            # and immediately place the entity at the intersection point. If we didn't click on any
            # MapObject, place the entity on the grid where we clicked.
            entries = vp.click(GeomNode.getDefaultCollideMask())
            if entries and len(entries) > 0:
                for i in range(len(entries)):
                    entry = entries[i]
                    # Don't backface cull if there is a billboard effect on or above this node
                    if not LEUtils.hasNetBillboard(entry.getIntoNodePath()):
                        surfNorm = entry.getSurfaceNormal(vp.cam).normalized()
                        rayDir = entry.getFrom().getDirection().normalized()
                        if surfNorm.dot(rayDir) >= 0:
                            # Backface cull
                            continue
                    # We clicked on an object, use the contact point as the
                    # location of our new entity.
                    self.pos = entry.getSurfacePoint(self.doc.render)
                    self.hasPlaced = True
                    # Create it!
                    self.confirm()
                    break
            else:
                # Didn't click on an object, intersect our mouse ray with the grid plane.
                plane = LPlane(0, 0, 1, 0)
                worldMouse = vp.viewportToWorld(vp.getMouse())
                theCamera = vp.cam.getPos(render)
                # Ensure that the camera and mouse positions are on opposite
                # sides of the plane, or else the entity would place behind us.
                sign1 = plane.distToPlane(worldMouse) >= 0
                sign2 = plane.distToPlane(theCamera) >= 0
                if sign1 != sign2:
                    pointOnPlane = Point3()
                    ret = plane.intersectsLine(pointOnPlane, theCamera, worldMouse)
                    if ret:
                        # Our mouse intersected the grid plane. Place an entity at the plane intersection point.
                        self.pos = pointOnPlane
                        self.hasPlaced = True
                        self.confirm()
            return

        # The user clicked in the 2D viewport, draw the visualization where they clicked.
        self.showVis()
        self.updatePosFromViewport(vp)
        self.mouseIsDown = True
        self.hasPlaced = True

    def mouseMoved(self, vp):
        if not vp:
            return
        if vp.is2D() and self.mouseIsDown:
            # If the mouse moved in the 2D viewport and the mouse is
            # currently pressed, update the visualization at the new position
            self.updatePosFromViewport(vp)

    def mouseUp(self):
        self.mouseIsDown = False

    def confirm(self):
        if not self.hasPlaced:
            return

        if self.applyRandomYaw:
            yaw = random.uniform(0, 360)
        else:
            yaw = 0

        ent = Entity(base.document.getNextID())
        ent.setClassname(self.classname)
        ent.np.setPos(self.pos)
        ent.np.setH(yaw)
        # Select the entity right away so we can conveniently move it around and
        # whatever without having to manually select it.
        base.actionMgr.performAction("Create entity",
            ActionGroup([
                Deselect(all = True),
                Create(base.document.world.id, ent),
                ChangeSelectionMode(SelectionType.Groups),
                Select([ent], False)
            ])
        )

        self.reset()

    def getMoveDelta(self, localDelta, vp):
        return vp.rotate(localDelta) * GridSettings.DefaultStep

    def moveUp(self):
        vp = base.viewportMgr.activeViewport
        if not vp or not vp.is2D():
            return

        self.updatePos(self.pos + self.getMoveDelta(Vec3.up(), vp))

    def moveDown(self):
        vp = base.viewportMgr.activeViewport
        if not vp or not vp.is2D():
            return

        self.updatePos(self.pos + self.getMoveDelta(Vec3.down(), vp))

    def moveLeft(self):
        vp = base.viewportMgr.activeViewport
        if not vp or not vp.is2D():
            return

        self.updatePos(self.pos + self.getMoveDelta(Vec3.left(), vp))

    def moveRight(self):
        vp = base.viewportMgr.activeViewport
        if not vp or not vp.is2D():
            return

        self.updatePos(self.pos + self.getMoveDelta(Vec3.right(), vp))

    def update(self):
        # Maintain a constant size for the 2D views
        for view in self.box.views:
            if view.viewport.is2D():
                view.np.setScale(self.size2D / view.viewport.zoom)
