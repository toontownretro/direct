from panda3d.core import GeomVertexFormat, GeomVertexWriter, Vec4, Point3

from .Geometry import Geometry
from .BoxView import BoxView

# An axis-aligned 3D box
class Box(Geometry):

    def __init__(self):
        Geometry.__init__(self, "box", GeomVertexFormat.getV3c4())
        self.color = Vec4(1, 1, 1, 1)
        self.mins = Point3(0)
        self.maxs = Point3(0)
        self.calcBoxVertices()

    def addView(self, primitiveType, drawMask, viewHpr = None, state = None):
        return Geometry.addView(self, BoxView(self, primitiveType, drawMask, viewHpr, state))

    def setMinMax(self, mins, maxs):
        self.mins = mins
        self.maxs = maxs
        self.calcBoxVertices()
        self.generateVertices()

    def setColor(self, color):
        self.color = color
        self.generateVertices()

    def calcBoxVertices(self):
        start = self.mins
        end = self.maxs
        topLeftBack = Point3(start.x, end.y, end.z)
        topRightBack = end
        topLeftFront = Point3(start.x, start.y, end.z)
        topRightFront = Point3(end.x, start.y, end.z)
        bottomLeftBack = Point3(start.x, end.y, start.z)
        bottomRightBack = Point3(end.x, end.y, start.z)
        bottomLeftFront = start
        bottomRightFront = Point3(end.x, start.y, start.z)

        self.vertexList = [
            topLeftBack, # 0
            topRightBack, # 1
            topLeftFront, # 2
            topRightFront, # 3
            bottomLeftBack, # 4
            bottomRightBack, # 5
            bottomLeftFront, # 6
            bottomRightFront # 7
        ]

    def generateVertices(self):
        self.vertexBuffer.setNumRows(8)

        vwriter = GeomVertexWriter(self.vertexBuffer, "vertex")
        cwriter = GeomVertexWriter(self.vertexBuffer, "color")

        for i in range(len(self.vertexList)):
            vwriter.setData3f(self.vertexList[i])
            cwriter.setData4f(self.color)

        Geometry.generateVertices(self)
