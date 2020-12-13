from panda3d.core import Point3, Vec3, NodePath, LineSegs, Vec4, \
    CollisionTraverser, CollisionHandlerQueue, CollisionBox, CollisionNode, \
    BitMask32, KeyboardButton

from .BoxTool import BoxAction, ResizeHandle
from .ToolOptions import ToolOptions
from direct.foundry.SelectionType import SelectionModeTransform
from direct.foundry.Ray import Ray
from direct.foundry.ViewportType import VIEWPORT_3D_MASK
from direct.foundry import LEUtils, LEGlobals
from direct.foundry.EditObjectProperties import EditObjectProperties
from direct.foundry.ActionGroup import ActionGroup
from direct.foundry.Create import Create
from direct.foundry.Select import Select
from .SelectTool import SelectTool
from direct.foundry import LEGlobals

from PyQt5 import QtWidgets

Ready = 0
Rollover = 1
Down = 2

Global = 0
Local = 1

class TransformToolOptions(ToolOptions):

    GlobalPtr = None
    @staticmethod
    def getGlobalPtr():
        self = TransformToolOptions
        if not self.GlobalPtr:
            self.GlobalPtr = TransformToolOptions()
        return self.GlobalPtr

    def __init__(self):
        ToolOptions.__init__(self)

        group = QtWidgets.QGroupBox("With Respect To", self)
        group.setLayout(QtWidgets.QFormLayout())
        globalBtn = QtWidgets.QRadioButton("Global", group)
        globalBtn.toggled.connect(self.__toggleGlobal)
        group.layout().addWidget(globalBtn)
        localBtn = QtWidgets.QRadioButton("Local", group)
        localBtn.toggled.connect(self.__toggleLocal)
        group.layout().addWidget(localBtn)

        self.globalBtn = globalBtn
        self.localBtn = localBtn

        self.layout().addWidget(group)

    def setTool(self, tool):
        ToolOptions.setTool(self, tool)

        if self.tool.wrtMode == Global:
            self.globalBtn.setChecked(True)
        elif self.tool.wrtMode == Local:
            self.localBtn.setChecked(True)

    def __toggleGlobal(self):
        self.tool.setWrtMode(Global)

    def __toggleLocal(self):
        self.tool.setWrtMode(Local)

class TransformWidgetAxis(NodePath):

    DotFade = True
    DotRange = [0.95, 0.99]
    OppositeDot = False

    def __init__(self, widget, axis):
        NodePath.__init__(self, "transformWidgetAxis")
        self.reparentTo(widget)
        self.widget = widget
        vec = Vec3(0)
        vec[axis] = 1.0
        self.direction = vec
        self.defaultColor = Vec4(vec[0], vec[1], vec[2], 1.0)
        self.rolloverColor = Vec4(vec + 0.5, 1.0)
        self.downColor = Vec4(vec - 0.5, 1.0)
        self.lookAt(vec)
        self.setTransparency(1)

        self.axisIdx = axis

        box = CollisionBox(*self.getClickBox())
        cnode = CollisionNode("pickBox")
        cnode.addSolid(box)
        cnode.setIntoCollideMask(LEGlobals.ManipulatorMask)
        cnode.setFromCollideMask(BitMask32.allOff())
        self.pickNp = self.attachNewNode(cnode)
        self.pickNp.setPythonTag("widgetAxis", self)

        self.state = Ready
        self.setState(Ready)

    def cleanup(self):
        self.widget = None
        self.direction = None
        self.defaultColor = None
        self.rolloverColor = None
        self.downColor = None
        self.axisIdx = None
        self.pickNp.removeNode()
        self.pickNp = None
        self.state = None
        self.removeNode()

    def update(self):
        if self.DotFade:
            camToAxis = self.getPos(base.render) - self.widget.vp.cam.getPos(base.render)
            camToAxis.normalize()

            dot = abs(camToAxis.dot(self.direction))
            inRange = dot >= self.DotRange[0] if not self.OppositeDot else dot <= self.DotRange[0]
            if inRange:
                alpha = LEGlobals.remapVal(dot, self.DotRange[0], self.DotRange[1], 1.0, 0.0)
                self.setAlphaScale(alpha)
            else:
                self.setAlphaScale(1)

    def getClickBox(self):
        return [Vec3(-1), Vec3(1)]

    def setState(self, state):
        if state != self.state:
            self.widget.tool.doc.update3DViews()
        self.state = state
        if state == Ready:
            self.setColorScale(self.defaultColor)
        elif state == Rollover:
            self.setColorScale(self.rolloverColor)
        elif state == Down:
            self.setColorScale(self.downColor)

class TransformWidget(NodePath):

    def __init__(self, tool):
        self.tool = tool
        NodePath.__init__(self, "transformWidget")
        self.widgetQueue = CollisionHandlerQueue()
        self.widgetTrav = CollisionTraverser()
        self.setLightOff(1)
        self.setFogOff(1)
        self.setDepthWrite(False, 1)
        self.setDepthTest(False, 1)
        self.setBin("unsorted", 60)
        self.hide(~VIEWPORT_3D_MASK)

        self.vp = None
        for vp in self.tool.doc.viewportMgr.viewports:
            if vp.is3D():
                self.vp = vp
                break

        self.activeAxis = None

        self.axes = {}
        for axis in (0, 1, 2):
            self.axes[axis] = self.createAxis(axis)

    def cleanup(self):
        self.tool = None
        self.widgetQueue = None
        self.widgetTrav = None
        self.vp = None
        self.activeAxis = None
        for axis in self.axes.values():
            axis.cleanup()
        self.axes = None
        self.removeNode()

    def createAxis(self, axis):
        return None

    def setActiveAxis(self, axis):
        if self.activeAxis:
            self.activeAxis.setState(Ready)
        if axis is None:
            self.activeAxis = None
        else:
            self.activeAxis = self.axes[axis]
            self.activeAxis.setState(Rollover)

    def update(self):
        distance = self.getPos(self.vp.cam).length()
        self.setScale(distance / 4)

        for _, axis in self.axes.items():
            axis.update()

        if self.tool.mouseIsDown or self.tool.doc.viewportMgr.activeViewport != self.vp:
            return

        self.setActiveAxis(None)
        entries = self.vp.click(LEGlobals.ManipulatorMask, self.widgetQueue,
                                self.widgetTrav, self)
        if entries and len(entries) > 0:
            entry = entries[0]
            axisObj = entry.getIntoNodePath().getPythonTag("widgetAxis")
            self.setActiveAxis(axisObj.axisIdx)

    def enable(self):
        self.reparentTo(self.tool.toolRoot)

    def disable(self):
        self.reparentTo(NodePath())

# Base class for a tool that transforms objects.
# Inherted by MoveTool, RotateTool, and ScaleTool
class BaseTransformTool(SelectTool):

    def __init__(self, mgr):
        SelectTool.__init__(self, mgr)
        self.hasWidgets = False
        self.widget = None
        self.toolRoot = self.doc.render.attachNewNode("xformToolRoot")
        self.toolVisRoot = self.toolRoot.attachNewNode("xformVisRoot")
        self.toolVisRoot.setTransparency(True)
        self.toolVisRoot.setColorScale(1, 1, 1, 0.5, 1)
        self.axis3DLines = None
        self.isTransforming = False
        self.xformObjects = []
        self.boxOriginOffset = Vec3(0, 0, 0)
        # With respect to mode. Gizmo is rotated differently
        # based on this mode.
        self.wrtMode = Global
        self.transformStart = Point3(0)
        self.preTransformStart = Point3(0)
        self.transformType = SelectionModeTransform.Off
        self.createWidget()

        self.options = TransformToolOptions.getGlobalPtr()

    def cleanup(self):
        self.hasWidgets = None
        self.widget.cleanup()
        self.widget = None
        self.toolRoot.removeNode()
        self.toolRoot = None
        self.toolVisRoot = None
        if self.axis3DLines:
            self.axis3DLines.removeNode()
        self.axis3DLines = None
        self.isTransforming = None
        self.xformObjects = None
        self.boxOriginOffset = None
        self.wrtMode = None
        self.transformStart = None
        self.preTransformStart = None
        self.transformType = None
        SelectTool.cleanup(self)

    def filterHandle(self, handle):
        if self.isTransforming:
            # Don't show handles if we're scaling in 3D
            return False
        return True

    def onBeginTransform(self, vp):
        pass

    def resizeBoxDrag(self):
        SelectTool.resizeBoxDrag(self)

        if self.state.action == BoxAction.Resizing and base.selectionMgr.hasSelectedObjects():
            if self.state.handle == ResizeHandle.Center:
                boxCenter = (self.state.boxStart + self.state.boxEnd) / 2.0
                self.setGizmoOrigin(boxCenter + self.boxOriginOffset)
            self.onSelectedBoxResize()

    def onSelectedBoxResize(self):
        pass

    def createWidget(self):
        pass

    def setBoxToSelection(self):
        self.state.boxStart = base.selectionMgr.selectionMins
        self.state.boxEnd = base.selectionMgr.selectionMaxs
        # Calculate an offset from the center of the box to the gizmo origin
        # so we can keep the box and gizmo in sync as they move.
        self.boxOriginOffset = self.getGizmoOrigin() - base.selectionMgr.selectionCenter
        self.state.action = BoxAction.Drawn
        self.resizeBoxDone()
        self.showBox()
        self.showText()

    def setBoxToVisRoot(self):
        self.toolVisRoot.calcTightBounds(self.state.boxStart, self.state.boxEnd, self.doc.render)
        self.state.action = BoxAction.Drawn
        self.resizeBoxDone()
        self.showBox()
        self.showText()

    def setWrtMode(self, mode):
        self.wrtMode = mode
        self.adjustGizmoAngles()

    def adjustGizmoAngles(self):
        if self.wrtMode == Global:
            # Look forward in world space
            self.setGizmoAngles(Vec3(0, 0, 0))

        elif self.wrtMode == Local:
            # Set the gizmo angles to the angles of the most
            # recently selected object.
            if base.selectionMgr.hasSelectedObjects():
                numSelections = base.selectionMgr.getNumSelectedObjects()
                selection = base.selectionMgr.selectedObjects[numSelections - 1]
                self.setGizmoAngles(selection.getAbsAngles())

    def handleSelectedObjectTransformChanged(self, entity):
        # This method unfortunately gets called when we change the transform on
        # the selected objects when finishing the move... changing
        # the widget point while applying the final move position
        # screws it up.
        if not self.isTransforming:
            self.calcWidgetPoint()

    def selectionChanged(self):
        if base.selectionMgr.hasSelectedObjects() \
            and base.selectionMgr.isTransformAllowed(self.transformType):
            if not self.hasWidgets:
                self.enableWidget()
            else:
                self.calcWidgetPoint()
        elif self.hasWidgets:
            self.disableWidget()
            self.maybeCancel()

    def calcWidgetPoint(self, updateBox = True):
        # Set the gizmo to the average origin of all the selected objects.
        avg = Point3(0)
        for obj in base.selectionMgr.selectedObjects:
            avg += obj.getAbsOrigin()
        avg /= len(base.selectionMgr.selectedObjects)
        self.setGizmoOrigin(avg)
        self.adjustGizmoAngles()
        if updateBox:
            self.setBoxToSelection()

    def mouseDown(self):
        SelectTool.mouseDown(self)
        if self.widget.activeAxis:
            self.widget.activeAxis.setState(Down)
            vp = base.viewportMgr.activeViewport
            if vp.is2D():
                self.transformStart = vp.viewportToWorld(vp.getMouse(), flatten = False)
            else:
                self.transformStart = self.getPointOnGizmo()
        self.preTransformStart = self.getGizmoOrigin()

    def mouseMove(self, vp):
        if vp and vp.is3D() and self.mouseIsDown and self.widget.activeAxis:
            if not self.isTransforming:
                self.createMoveVis()
                self.isTransforming = True
                self.onBeginTransform(vp)
            self.onMouseMoveTransforming3D(vp)
            self.doc.updateAllViews()
        else:
            if not self.isTransforming and self.state.action in [BoxAction.DownToResize, BoxAction.Resizing]:
                self.createMoveVis()
                self.isTransforming = True
                self.onBeginTransform(vp)
            self.onMouseMoveTransforming2D(vp)
            SelectTool.mouseMove(self, vp)

    def onMouseMoveTransforming2D(self, vp):
        pass

    def onMouseMoveTransforming3D(self, vp):
        pass

    def getGizmoDirection(self, axis):
        quat = self.toolRoot.getQuat(NodePath())
        if axis == 0:
            return quat.getRight()
        elif axis == 1:
            return quat.getForward()
        else:
            return quat.getUp()

    def getGizmoOrigin(self):
        return self.toolRoot.getPos(NodePath())

    def setGizmoOrigin(self, origin):
        self.toolRoot.setPos(NodePath(), origin)

    def setGizmoAngles(self, angles):
        self.toolRoot.setHpr(NodePath(), angles)

    def getGizmoRay(self, axis):
        direction = self.getGizmoDirection(axis)
        origin = self.getGizmoOrigin()
        return Ray(origin, direction)

    def getPointOnGizmo(self):
        vp = base.viewportMgr.activeViewport
        if not vp or not vp.is3D():
            return

        axis = self.widget.activeAxis.axisIdx
        gray = self.getGizmoRay(axis)
        mray = vp.getMouseRay()
        # Move into world space
        mray.xform(vp.cam.getMat(NodePath()))

        distance = LEUtils.closestDistanceBetweenLines(gray, mray)

        return gray.origin + (gray.direction * -gray.t)

    def createMoveVis(self):
        # Instance each selected map object to the vis root
        for obj in base.selectionMgr.selectedObjects:
            instRoot = NodePath("instRoot")
            inst = obj.np.instanceTo(instRoot)
            instRoot.wrtReparentTo(self.toolVisRoot)
            self.xformObjects.append((obj, instRoot, inst))

        # Show an infinite line along the axis we are moving the object
        # if we are using the 3D view
        if self.widget.activeAxis:
            axis = self.widget.activeAxis.axisIdx
            segs = LineSegs()
            col = Vec4(0, 0, 0, 1)
            col[axis] = 1.0
            segs.setColor(col)
            p = Point3(0)
            p[axis] = -1000000
            segs.moveTo(p)
            p[axis] = 1000000
            segs.drawTo(p)
            self.axis3DLines = self.toolRoot.attachNewNode(segs.create())
            self.axis3DLines.setLightOff(1)
            self.axis3DLines.setFogOff(1)

        self.widget.stash()

    def destroyMoveVis(self):
        for obj, instRoot, inst in self.xformObjects:
            instRoot.removeNode()
        self.xformObjects = []
        if self.axis3DLines:
            self.axis3DLines.removeNode()
            self.axis3DLines = None
        self.widget.unstash()

    def mouseUp(self):
        SelectTool.mouseUp(self)
        if self.widget.activeAxis:
            self.widget.activeAxis.setState(Rollover)

        if self.isTransforming:
            vp = base.viewportMgr.activeViewport
            if vp.mouseWatcher.isButtonDown(KeyboardButton.shift()):
                # Clone when shift is held
                self.onFinishTransformingClone()
            else:
                self.onFinishTransforming()
            self.onTransformDone()
            self.destroyMoveVis()
            base.selectionMgr.updateSelectionBounds()
        self.isTransforming = False

    def onTransformDone(self):
        pass

    def onFinishTransformingClone(self):
        # Clone the selections and set them to the transform the user
        # has chosen.
        copies = []
        actions = []
        for obj, _, inst in self.xformObjects:
            copy = obj.copy(base.document.idGenerator)
            copy.updateProperties(self.getUpdatedProperties(obj, inst))
            actions.append(Create(obj.parent.id, copy))
            copies.append(copy)
        actions.append(Select(copies, True))
        base.actionMgr.performAction("Duplicate %i object(s)" % len(copies),
            ActionGroup(actions))

    def onFinishTransforming(self):
        actions = []
        for obj, _, inst in self.xformObjects:
            action = EditObjectProperties(obj, self.getUpdatedProperties(obj, inst))
            actions.append(action)
        base.actionMgr.performAction("%s %i object(s)" % (self.getActionName(), len(self.xformObjects)),
            ActionGroup(actions))

    def getActionName(self):
        return "Transform"

    def getUpdatedProperties(self, obj, inst):
        return {}

    def update(self):
        SelectTool.update(self)
        if self.hasWidgets:
            self.widget.update()
            if self.widget.activeAxis or self.state.action in [BoxAction.ReadyToResize, BoxAction.DownToResize]:
                self.suppressSelect = True
            else:
                self.suppressSelect = False
        else:
            self.suppressSelect = False

    def enableWidget(self):
        self.calcWidgetPoint()
        self.widget.enable()
        self.hasWidgets = True

    def disableWidget(self):
        self.widget.disable()
        self.hasWidgets = False

    def activate(self):
        SelectTool.activate(self)
        # The transform may have been changed using the object properties panel.
        # Intercept this event to update our gizmo and stuff.
        self.accept('selectedObjectTransformChanged', self.handleSelectedObjectTransformChanged)
        # Same with bounds
        self.accept('selectedObjectBoundsChanged', self.handleSelectedObjectTransformChanged)

    def enable(self):
        SelectTool.enable(self)
        if base.selectionMgr.hasSelectedObjects() \
            and base.selectionMgr.isTransformAllowed(self.transformType):
            self.enableWidget()

    def disable(self):
        SelectTool.disable(self)
        self.disableWidget()
        if self.isTransforming:
            self.destroyMoveVis()
        self.isTransforming = False
