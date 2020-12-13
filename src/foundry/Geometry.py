from panda3d.core import GeomVertexData, NodePath, GeomEnums, GeomVertexFormat, OmniBoundingVolume

from .GeomView import GeomView

# Base class for procedural geometry types
class Geometry:

    def __init__(self, name, format = GeomVertexFormat.getV3()):
        self.views = []
        self.vertexBuffer = GeomVertexData(name + "-vdata", format, GeomEnums.UHDynamic)

        self.np = NodePath(name)
        self.np.node().setBounds(OmniBoundingVolume())
        self.np.node().setFinal(1)
        # taha was here

    def generateIndices(self, firstVertex = 0, numVerts = None):
        if numVerts is None:
            numVerts = self.vertexBuffer.getNumRows()
            clear = True
        else:
            clear = False
        for view in self.views:
            view.generateIndices(firstVertex, numVerts, clear)

    def generateGeometry(self):
        self.generateVertices()
        self.generateIndices()

    def generateVertices(self):
        pass

    def cleanup(self):
        for view in self.views:
            view.cleanup()
        self.views = None
        self.np.removeNode()
        self.np = None
        self.vertexBuffer = None

    def addView(self, view):
        self.views.append(view)
        return view

    def removeView(self, view):
        if isinstance(view, int):
            viewObj = self.views[view]
        else:
            viewObj = view

        viewObj.cleanup()
        self.views.remove(viewObj)
