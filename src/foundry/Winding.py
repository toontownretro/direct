from panda3d.core import Vec3, Point3

from direct.foundry import LEGlobals

from .Line import Line
from . import PlaneClassification
from .Plane import Plane

class Winding:

    def __init__(self, vertices, plane):
        self.vertices = vertices
        self.plane = plane

    @staticmethod
    def fromVertices(vertices):
        poly = Winding(vertices, Plane.fromVertices(vertices[0], vertices[1], vertices[2]))
        poly.simplify()
        return poly

    # Creates a huge quadrilateral winding given a plane.
    @staticmethod
    def fromPlaneAndRadius(plane, radius = 32768):
        normal = plane.getNormal()
        dist = -plane.getW()

        # Find the major axis
        x = plane.getClosestAxisToNormal()
        up = Vec3.unitX() if x == Vec3.unitZ() else Vec3.unitZ()

        v = up.dot(normal)
        up = LEGlobals.extrude(up, -v, normal)
        up.normalize()

        org = normal * dist

        right = up.cross(normal)

        up = up * radius
        right = right * radius

        # Project a really big axis aligned box onto the plane
        verts = [
            org - right + up,
            org + right + up,
            org + right - up,
            org - right - up
        ]

        poly = Winding(verts, plane)

        return poly

    def isValid(self):
        for vert in self.vertices:
            if self.plane.onPlane(vert) != 0:
                # Vert doesn't lie within the plane.
                return False

        return True

    def simplify(self):
        # Remove colinear vertices
        i = 0
        while 1:
            numVerts = len(self.vertices) - 2
            if i >= numVerts:
                break

            v1 = self.vertices[i]
            v2 = self.vertices[i + 2]
            p = self.vertices[i + 1]
            line = Line(v1, v2)
            # If the midpoint is on the line, remove it
            if line.closestPoint(p).almostEqual(p):
                del self.vertices[i + 1]

            i += 1

    def xform(self, mat):
        for i in range(len(self.vertices)):
            self.vertices[i] = mat.xformPoint(self.vertices[i])

        self.plane = Plane.fromVertices(self.vertices[0], self.vertices[1], self.vertices[2])

    def isConvex(self, epsilon = 0.001):
        for i in range(len(self.vertices)):
            v1 = self.vertices[i]
            v2 = self.vertices[(i + 1) % len(self.vertices)]
            v3 = self.vertices[(i + 2) % len(self.vertices)]
            l1 = (v1 - v2).normalized()
            l2 = (v3 - v2).normalized()
            cross = l1.cross(l2)
            if abs(self.plane.distToPlane(v2 + cross)) > epsilon:
                return False

        return True

    def getOrigin(self):
        return self.plane.getNormal() * -self.plane.getW()

    def classifyAgainstPlane(self, plane):
        front = 0
        back = 0
        onplane = 0
        count = len(self.vertices)

        for i in range(count):
            test = plane.onPlane(self.vertices[i])
            if test <= 0:
                back += 1
            if test >= 0:
                front += 1
            if test == 0:
                onplane += 1

        if onplane == count:
            return PlaneClassification.OnPlane
        if front == count:
            return PlaneClassification.Front
        if back == count:
            return PlaneClassification.Back

        return PlaneClassification.Spanning

    def splitInPlace(self, clipPlane, epsilon = 0.01):
        front = self.split(clipPlane, epsilon)
        if front:
            self.vertices = list(front.vertices)
            self.plane = Plane(front.plane)
            return True
        return False

    def split(self, plane, epsilon = 0.01):
        dists = []
        sides = []
        counts = [0, 0, 0]

        norm = plane.getNormal()
        dist = -plane.getW()

        # Determine sides for each point
        for i in range(len(self.vertices)):
            dot = self.vertices[i].dot(norm)
            dot -= dist
            dists.append(dot)
            if dot > epsilon:
                sides.append(PlaneClassification.Front)
            elif dot < -epsilon:
                sides.append(PlaneClassification.Back)
            else:
                sides.append(PlaneClassification.OnPlane)
            counts[sides[i]] += 1

        sides.append(sides[0])
        dists.append(dists[0])

        if not counts[0] and not counts[1]:
            return self

        if not counts[0]:
            return None

        if not counts[1]:
            return self

        verts = []
        for i in range(len(self.vertices)):
            p1 = self.vertices[i]
            if sides[i] in [PlaneClassification.Front, PlaneClassification.OnPlane]:
                verts.append(p1)
                if sides[i] == PlaneClassification.OnPlane:
                    continue

            if sides[i+1] in [PlaneClassification.OnPlane, sides[i]]:
                continue

            # Generate a split point
            if i == len(self.vertices) - 1:
                p2 = self.vertices[0]
            else:
                p2 = self.vertices[i+1]

            mid = Point3(0)
            dot = dists[i] / (dists[i]-dists[i+1])
            for j in range(3):
                # Avoid round off error when possible
                if norm[j] == 1:
                    mid[j] = dist
                elif norm[j] == -1:
                    mid[j] = -dist
                else:
                    mid[j] = p1[j] + dot*(p2[j]-p1[j])

            verts.append(mid)

        return Winding.fromVertices(verts)

    def roundPoints(self, epsilon = 0.01):
        #
        # Round all points in the winding that are within `epsilon` of
        # integer values
        #
        for i in range(len(self.vertices)):
            for j in range(3):
                v = self.vertices[i][j]
                v1 = round(v)
                if (v != v1) and abs(v - v1) < epsilon:
                    self.vertices[i][j] = v1

    def flip(self):
        self.vertices.reverse()
        self.plane.flip()
