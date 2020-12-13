from .BaseTransformTool import BaseTransformTool, TransformWidget, TransformWidgetAxis
from direct.foundry.SelectionType import SelectionModeTransform
from direct.foundry import LEUtils
from direct.foundry.EditObjectProperties import EditObjectProperties
from direct.foundry.ActionGroup import ActionGroup
from direct.foundry.KeyBind import KeyBind

from panda3d.core import LineSegs, Vec3, AntialiasAttrib, LPlane, Point3, KeyboardButton

class RotateWidgetAxis(TransformWidgetAxis):

    DotRange = [0.05, 0.01]
    OppositeDot = True

    def __init__(self, widget, axis):
        TransformWidgetAxis.__init__(self, widget, axis)
        segs = LineSegs()
        segs.setThickness(2)
        vertices = LEUtils.circle(0, 0, 1, 64)
        for i in range(len(vertices)):
            x1, y1 = vertices[i]
            x2, y2 = vertices[(i + 1) % len(vertices)]
            segs.moveTo(x1, 0, y1)
            segs.drawTo(x2, 0, y2)
        self.axisCircle = self.attachNewNode(segs.create())
        self.axisCircle.setAntialias(AntialiasAttrib.MLine)

    def cleanup(self):
        self.axisCircle.removeNode()
        self.axisCircle = None
        TransformWidgetAxis.cleanup(self)

    def getClickBox(self):
        return [Vec3(-1, -0.2, -1), Vec3(1, 0.2, 1)]

class RotateWidget(TransformWidget):

    def createAxis(self, axis):
        return RotateWidgetAxis(self, axis)

class RotateTool(BaseTransformTool):

    Name = "Rotate"
    ToolTip = "Rotate Tool"
    KeyBind = KeyBind.RotateTool
    Icon = "icons/editor-rotate.png"

    def __init__(self, mgr):
        BaseTransformTool.__init__(self, mgr)
        self.transformType = SelectionModeTransform.Rotate

    def createWidget(self):
        self.widget = RotateWidget(self)

    def getActionName(self):
        return "Rotate"

    def getUpdatedProperties(self, obj, inst):
        transform = inst.getTransform(obj.np.getParent())
        return {"origin": Point3(transform.getPos()),
                "angles": Vec3(transform.getHpr())}

    def onTransformDone(self):
        self.toolVisRoot.setHpr(Vec3(0))
        self.setBoxToSelection()

    def getPointOnGizmo(self):
        vp = base.viewportMgr.activeViewport
        if not vp or not vp.is3D():
            return

        axis = self.widget.activeAxis
        axisIdx = axis.axisIdx

        direction = self.getGizmoDirection(axisIdx)
        plane = LPlane(direction, self.getGizmoOrigin())

        worldMouse = vp.viewportToWorld(vp.getMouse())

        intersection = Point3()
        ret = plane.intersectsLine(intersection, vp.cam.getPos(self.doc.render), worldMouse)
        if ret:
            # Project intersection point onto circle's circumference.
            point = self.getGizmoOrigin() + (intersection - self.getGizmoOrigin()).normalized()
            return point
        else:
            return Point3(0)

    def onMouseMoveTransforming3D(self, vp):
        now = self.getPointOnGizmo()

        gizmoOrigin = self.getGizmoOrigin()
        gizmoDir = self.getGizmoDirection(self.widget.activeAxis.axisIdx)
        ref = Vec3.forward()
        if gizmoDir == ref:
            ref = Vec3.right()

        nowVec = Vec3(now - gizmoOrigin).normalized()
        origVec = Vec3(self.transformStart - gizmoOrigin).normalized()

        axisToHprAxis = {
            0: 1, # pitch
            1: 2, # roll
            2: 0 # yaw
        }

        snap = not vp.mouseWatcher.isButtonDown(KeyboardButton.shift())

        origAngle = origVec.signedAngleDeg(ref, self.getGizmoDirection(self.widget.activeAxis.axisIdx))
        angle = nowVec.signedAngleDeg(ref, self.getGizmoDirection(self.widget.activeAxis.axisIdx))
        hpr = Vec3(0)
        if snap:
            ang = round(-(angle - origAngle) / 15) * 15
        else:
            ang = -(angle - origAngle)
        hpr[axisToHprAxis[self.widget.activeAxis.axisIdx]] = ang
        self.toolVisRoot.setHpr(hpr)
