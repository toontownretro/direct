from panda3d.core import Vec3

from . import PlaneClassification

class Line:

    def __init__(self, start, end):
        self.start = start
        self.end = end

    def reverse(self):
        temp = self.start
        self.start = self.end
        self.end = temp

    def closestPoint(self, point):
        delta = self.end - self.start
        den = delta.lengthSquared()
        if den == 0:
            return self.start # start and end are the same

        numPoint = point - self.start
        numPoint.componentwiseMult(delta)
        num = numPoint.x + numPoint.y + numPoint.z
        u = num / den

        if u < 0:
            return self.start # point is before the segment start
        if u > 1:
            return self.end # point is after the segment end

        return self.start + (delta * u)

    def classifyAgainstPlane(self, plane):
        start = plane.distToPlane(self.start)
        end = plane.distToPlane(self.end)

        if start == 0 and end == 0:
            return PlaneClassification.OnPlane
        if start <= 0 and end <= 0:
            return PlaneClassification.Back
        if start >= 0 and end >= 0:
            return PlaneClassification.Front

        return PlaneClassification.Spanning

    def xform(self, mat):
        self.start = mat.xformPointGeneral(self.start)
        self.end = mat.xformPointGeneral(self.end)

    def almostEqual(self, other, delta = 0.0001):
        return (self.start.almostEqual(other.start, delta) and self.end.almostEqual(other.end, delta)) \
            or (self.end.almostEqual(other.start, delta) and self.start.almostEqual(other.end, delta))

    def equals(self, other):
        if self == other:
            return True

        return (self.start == other.start and self.end == other.end) \
            or (self.start == other.end and self.end == other.start)
