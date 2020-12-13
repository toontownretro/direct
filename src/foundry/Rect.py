from panda3d.core import GeomVertexFormat, Vec4, Point3, GeomVertexWriter

from .Geometry import Geometry
from .PolygonView import PolygonView

# A flat rectangle with color
class Rect(Geometry):

    def __init__(self):
        Geometry.__init__(self, "rect",  GeomVertexFormat.getV3c4())
        self.color = Vec4(1, 1, 1, 1)
        self.mins = Point3(0)
        self.maxs = Point3(0)

    def addView(self, primitiveType, drawMask, viewHpr = None, state = None):
        return Geometry.addView(self, PolygonView(self, primitiveType, drawMask, viewHpr, state))

    def setMinMax(self, mins, maxs):
        self.mins = mins
        self.maxs = maxs
        self.generateVertices()

    def setColor(self, color):
        self.color = color
        self.generateVertices()

    def generateVertices(self):

        self.vertexBuffer.setNumRows(4)

        vwriter = GeomVertexWriter(self.vertexBuffer, "vertex")
        cwriter = GeomVertexWriter(self.vertexBuffer, "color")

        vwriter.setData3f(self.mins.x, 0, self.mins.z)
        cwriter.setData4f(self.color)

        vwriter.setData3f(self.mins.x, 0, self.maxs.z)
        cwriter.setData4f(self.color)

        vwriter.setData3f(self.maxs.x, 0, self.maxs.z)
        cwriter.setData4f(self.color)

        vwriter.setData3f(self.maxs.x, 0, self.mins.z)
        cwriter.setData4f(self.color)

        Geometry.generateVertices(self)
