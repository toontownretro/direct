from panda3d.core import GeomTriangles, GeomLines, GeomLinestrips, NodePath, GeomNode, Geom, GeomEnums
from panda3d.core import BitMask32

# Represents a single "view" of a procedural Geometry.
class GeomView:

    Triangles = 0
    Lines = 1
    LineStrips = 2

    IndicesForPrimitiveType = {
        Triangles: GeomTriangles,
        Lines: GeomLines,
        LineStrips: GeomLinestrips
    }

    def __init__(self, geometry, primitiveType, drawMask,
                 viewHpr = None, renderState = None):
        self.geometry = geometry
        self.drawMask = drawMask
        self.primitiveType = primitiveType
        self.indices = self.IndicesForPrimitiveType[self.primitiveType](GeomEnums.UHStatic)
        self.geom = Geom(geometry.vertexBuffer)
        self.geom.addPrimitive(self.indices)
        self.np = NodePath(GeomNode("geomView"))
        self.np.node().addGeom(self.geom)
        self.np.hide(~drawMask)
        self.np.reparentTo(self.geometry.np)
        if viewHpr is not None:
            self.np.setHpr(viewHpr)
        if renderState is not None:
            self.np.setState(renderState)

    def clear(self):
        self.indices.clearVertices()
        self.np.node().removeAllGeoms()

    def generateTriangleIndices(self, firstVertex, numVerts):
        raise NotImplementedError

    def generateLineIndices(self, firstVertex, numVerts):
        raise NotImplementedError

    def generateLineStripIndices(self, firstVertex, numVerts):
        raise NotImplementedError

    def generateIndices(self, firstVertex, numVerts, clear):
        if clear:
            self.indices.clearVertices()
        if self.primitiveType == self.Triangles:
            self.generateTriangleIndices(firstVertex, numVerts)
        elif self.primitiveType == self.Lines:
            self.generateLineIndices(firstVertex, numVerts)
        elif self.primitiveType == self.LineStrips:
            self.generateLineStripIndices(firstVertex, numVerts)
        else:
            raise NotImplementedError

    def cleanup(self):
        self.np.removeNode()
        self.np = None
        self.indices = None
        self.geom = None
        self.geometry = None
        self.drawMask = None
        self.primitiveType = None
