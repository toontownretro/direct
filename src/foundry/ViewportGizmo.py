from panda3d.core import LineSegs, Vec4, Point3, TextNode, Vec3

# Widget that shows which direction the camera is looking in the 3D viewport.
class ViewportGizmo:

    def __init__(self, vp):
        self.vp = vp
        axes = self.vp.getGizmoAxes()

        self.np = self.vp.a2dBottomLeft.attachNewNode("viewAxisWidget")
        self.np.setScale(0.14)
        self.np.setPos(0.19, 0, 0.19)

        if 0 in axes:
            # X line
            self.xNp = self.makeGizmoAxis(0, "X", 1.2)

        if 1 in axes:
            # Y line
            self.yNp = self.makeGizmoAxis(1, "Y")

        if 2 in axes:
            # Z line
            self.zNp = self.makeGizmoAxis(2, "Z")

    def cleanup(self):
        self.vp = None
        if hasattr(self, 'xNp'):
            self.xNp.removeNode()
            self.xNp = None
        if hasattr(self, 'yNp'):
            self.yNp.removeNode()
            self.yNp = None
        if hasattr(self, 'zNp'):
            self.zNp.removeNode()
            self.zNp = None
        self.np.removeNode()
        self.np = None

    def makeGizmoAxis(self, axis, text, textOffset = 1.1):
        color = Vec4(0, 0, 0, 1)
        color[axis] = 1

        pos = Vec3(0, 1, 0)
        if axis == 1:
            pos[1] = -pos[1]

        if axis == 1:
            textOffset = -textOffset

        direction = Vec3(0)
        direction[axis] = 1

        segs = LineSegs()
        segs.setColor(color)
        segs.moveTo(Point3(0))
        segs.drawTo(pos)
        np = self.np.attachNewNode(segs.create())
        np.lookAt(direction)
        tn = TextNode('gizmoAxis%iText' % axis)
        tn.setTextColor(color)
        tn.setAlign(TextNode.ACenter)
        tn.setText(text)
        tnnp = np.attachNewNode(tn.generate())
        tnnp.setY(textOffset)
        tnnp.setBillboardPointEye()
        tnnp.setScale(0.5)

        return np
