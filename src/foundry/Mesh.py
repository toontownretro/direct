from panda3d.core import GeomVertexFormat, Vec3, LTexCoord, NodePath, RenderState, GeomEnums, GeomVertexData, \
    GeomVertexWriter, InternalName

from .Geometry import Geometry
from .PolygonView import PolygonView

class MeshVertex:

    def __init__(self, pos, normal, texcoord):
        self.pos = pos
        self.normal = normal
        self.texcoord = texcoord

# Dynamic mesh with an arbitrary number of polygons.
class Mesh:

    def __init__(self):
        self.views = []
        self.vertexBuffer = GeomVertexData('mesh-vdata', GeomVertexFormat.getV3n3t2(), GeomEnums.UHDynamic)
        self.np = NodePath("mesh")

        self.vwriter = None
        self.twriter = None
        self.nwriter = None

    def addView(self, primitiveType, drawMask, state = None):
        self.views.append(PolygonView(self, primitiveType, drawMask, renderState=state))

    def begin(self, numVerts):
        self.vertexBuffer.uncleanSetNumRows(numVerts)
        for view in self.views:
            view.clear()
        self.vwriter = GeomVertexWriter(self.vertexBuffer, InternalName.getVertex())
        self.twriter = GeomVertexWriter(self.vertexBuffer, InternalName.getTexcoord())
        self.nwriter = GeomVertexWriter(self.vertexBuffer, InternalName.getNormal())

    def end(self):
        self.vwriter = None
        self.nwriter = None
        self.twriter = None

    def addFace(self, meshVertices, state = RenderState.makeEmpty()):
        row = self.vwriter.getWriteRow()
        for vert in meshVertices:
            self.vwriter.setData3f(vert.pos)
            self.nwriter.setData3f(vert.normal)
            self.twriter.setData2f(vert.texcoord)
        for view in self.views:
            view.generateIndices()
