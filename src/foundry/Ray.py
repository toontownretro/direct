class Ray:

    def __init__(self, origin, direction):
        self.origin = origin
        self.direction = direction
        self.t = 0

    def xform(self, mat):
        self.origin = mat.xformPoint(self.origin)
        self.direction = mat.xformVec(self.direction)

    def getOrigin(self):
        return self.origin

    def getDirection(self):
        return self.direction
