from panda3d.core import GeomVertexFormat, GeomVertexWriter, Point3, Vec4

from .Geometry import Geometry
from .PolygonView import PolygonView
from enum import IntEnum

class HandleType(IntEnum):
    Square = 0
    Circle = 1

class SquareHandlesView(PolygonView):

    def __init__(self, geometry, primitiveType, drawMask, viewHpr, state = None):
        PolygonView.__init__(self, geometry, primitiveType, drawMask, viewHpr, state)

    def generateTriangleIndices(self, firstVertex, numVerts):
        vtx = 0
        numHandles = len(self.geometry.handleOrigins)
        for i in range(numHandles):
            for j in range(2):
                PolygonView.generateTriangleIndices(self, vtx, 4)
                vtx += 4

class Handles(Geometry):

    Black = Vec4(0, 0, 0, 1)
    White = Vec4(1, 1, 1, 1)

    def __init__(self, handleType):
        Geometry.__init__(self, "handles", GeomVertexFormat.getV3c4())
        self.radius = 1.0
        self.zoom = 1.0
        self.handleOrigins = [
            Point3(0),
            Point3(0),
            Point3(0),
            Point3(0),
            Point3(0),
            Point3(0),
            Point3(0),
            Point3(0)
        ]
        self.handleType = handleType

    def addView(self, primitiveType, drawMask, viewHpr = None, renderState = None):
        if self.handleType == HandleType.Square:
            return Geometry.addView(
                self, SquareHandlesView(self, primitiveType, drawMask, viewHpr, renderState))
        return None

    def setHandles(self, handles, zoom):
        if handles == self.handleOrigins and zoom == self.zoom:
            return
        self.zoom = zoom
        self.handleOrigins = list(handles)
        if len(self.handleOrigins) == 0:
            self.np.hide()
            return
        else:
            self.np.show()
        self.generateVertices()

    def generateVertices(self):

        if self.handleType == HandleType.Square:
            self.vertexBuffer.setNumRows(len(self.handleOrigins) * 8)
            vwriter = GeomVertexWriter(self.vertexBuffer, "vertex")
            cwriter = GeomVertexWriter(self.vertexBuffer, "color")
            radius = self.radius / self.zoom
            add = radius * 0.08

            for origin in self.handleOrigins:
                ul = Point3(origin.x - radius, 0, origin.z - radius)
                lr = Point3(origin.x + radius + add, 0, origin.z + radius + add)

                # Border
                vwriter.setData3f(ul.x, 0.1, ul.z)
                cwriter.setData4f(self.Black)
                vwriter.setData3f(lr.x, 0.1, ul.z)
                cwriter.setData4f(self.Black)
                vwriter.setData3f(lr.x, 0.1, lr.z)
                cwriter.setData4f(self.Black)
                vwriter.setData3f(ul.x, 0.1, lr.z)
                cwriter.setData4f(self.Black)

                ul.x += add
                ul.z += add
                lr.x -= add
                lr.z -= add

                vwriter.setData3f(ul.x, 0, ul.z)
                cwriter.setData4f(self.White)
                vwriter.setData3f(lr.x, 0, ul.z)
                cwriter.setData4f(self.White)
                vwriter.setData3f(lr.x, 0, lr.z)
                cwriter.setData4f(self.White)
                vwriter.setData3f(ul.x, 0, lr.z)
                cwriter.setData4f(self.White)

        Geometry.generateVertices(self)
