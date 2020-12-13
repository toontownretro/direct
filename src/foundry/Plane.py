from panda3d.core import LPlane, Vec3

class Plane(LPlane):

    @staticmethod
    def fromVertices(p1, p2, p3):
        ab = p1 - p2
        ac = p3 - p2
        normal = ab.cross(ac).normalized()
        dist = normal.dot(p1)

        return Plane(normal[0], normal[1], normal[2], -dist)

    def getIntersectionPoint(self, start, end, ignoreDirection = False, ignoreSegment = False):
        direction = end - start
        denom = -self.getNormal().dot(direction)
        num = self.getNormal().dot(start - self.getNormal() * -self.getW())
        if abs(denom) < 0.00001 or (not ignoreDirection and denom < 0):
            return None

        u = num / denom
        if not ignoreSegment and (u < 0 or u > 1):
            return None

        return start + (direction * u)

    def onPlane(self, point, epsilon = 0.5):
        res = self.distToPlane(point)
        if abs(res) < epsilon:
            return 0

        if res < 0:
            return -1
        return 1

    def getClosestAxisToNormal(self):
        # VHE Prioritizes the axes in order of X, Y, Z

        norm = self.getNormal()
        norm[0] = abs(norm[0])
        norm[1] = abs(norm[1])
        norm[2] = abs(norm[2])

        if norm.x >= norm.y and norm.x >= norm.z:
            return Vec3.unitX()
        if norm.y >= norm.z:
            return Vec3.unitY()
        return Vec3.unitZ()

    @staticmethod
    def intersect(p1, p2, p3):

        # Get the intersection point of 3 planes
        c1 = p2.getNormal().cross(p3.getNormal())
        c2 = p3.getNormal().cross(p1.getNormal())
        c3 = p1.getNormal().cross(p2.getNormal())

        denom = p1.getNormal().dot(c1)
        if denom < 0.00001:
            return None

        numer = (-p1[3] * c1) + (-p2[3] * c2) + (-p3[3] * c3)
        return numer / denom
