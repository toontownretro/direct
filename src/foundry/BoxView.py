from .GeomView import GeomView

class BoxView(GeomView):

    VertexIndices = [
        [2, 3, 7, 6],
        [1, 0, 4, 5],
        [0, 2, 6, 4],
        [3, 1, 5, 7],
        [0, 1, 3, 2],
        [6, 7, 5, 4]
    ]

    def generateTriangleIndices(self, firstVertex, numVerts):
        for face in self.VertexIndices:
            for i in range(1, 3):
                self.indices.addVertices(
                    face[0],
                    face[i],
                    face[i + 1])
                self.indices.closePrimitive()

    def generateLineStripIndices(self, firstVertex, numVerts):
        for face in self.VertexIndices:
            for i in range(4):
                self.indices.addVertex(face[i])
            # Add the first vertex again to close the loop
            self.indices.addVertex(face[0])
            self.indices.closePrimitive()

    def generateLineIndices(self, firstVertex, numVerts):
        for face in self.VertexIndices:
            for i in range(1, 4):
                self.indices.addVertices(
                    face[i - 1],
                    face[i])
                self.indices.closePrimitive()
            self.indices.addVertices(face[0], face[3])
            self.indices.closePrimitive()
