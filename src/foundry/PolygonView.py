from .GeomView import GeomView

# This view generates indices for polygons.
class PolygonView(GeomView):

    def generateTriangleIndices(self, firstVertex, numVerts):
        for i in range(firstVertex + 1, firstVertex + (numVerts - 1)):
            self.indices.addVertices(firstVertex, i, i + 1)
            self.indices.closePrimitive()

    def generateLineStripIndices(self, firstVertex, numVerts):
        for i in range(firstVertex, firstVertex + numVerts):
            self.indices.addVertex(i)
        # Add the first vertex again to close the loop
        self.indices.addVertex(firstVertex)
        self.indices.closePrimitive()

    def generateLineIndices(self, firstVertex, numVerts):
        for i in range(firstVertex + 1, firstVertex + numVerts):
            self.indices.addVertices(i - 1, i)
            self.indices.closePrimitive()
        # Add the last line to close the loop
        self.indices.addVertices(firstVertex, numVerts - 1)
        self.indices.closePrimitive()
