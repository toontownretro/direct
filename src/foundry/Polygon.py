from panda3d.core import GeomVertexFormat, GeomVertexWriter, Vec4

from .Geometry import Geometry
from .PolygonView import PolygonView

class Polygon(Geometry):

    def __init__(self):
        Geometry.__init__(self, "polygon", GeomVertexFormat.getV3c4())
        self.vertices = []
        self.color = Vec4(1, 1, 1, 1)

    def addView(self, primitiveType, drawMask, viewHpr = None, state = None):
        return Geometry.addView(self, PolygonView(self, primitiveType, drawMask, viewHpr, state))

    def setVertices(self, verts):
        self.vertices = verts
        self.generateGeometry()

    def addVertex(self, point):
        self.vertices.append(point)
        self.generateGeometry()

    def setColor(self, color):
        self.color = color
        self.generateVertices()

    def generateVertices(self):
        self.vertexBuffer.setNumRows(len(self.vertices))

        vwriter = GeomVertexWriter(self.vertexBuffer, "vertex")
        cwriter = GeomVertexWriter(self.vertexBuffer, "color")
        for i in range(len(self.vertices)):
           vwriter.setData3f(self.vertices[i])
           cwriter.setData4f(self.color)

        Geometry.generateVertices(self)
