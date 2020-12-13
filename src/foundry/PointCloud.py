from panda3d.core import BoundingBox, Point3

# A collection of points
class PointCloud:

    def __init__(self, points = []):
        self.points = points
        self.calcBoundingBox()

    def addPoint(self, point):
        if point not in self.points:
            self.points.append(point)
            self.calcBoundingBox()

    def removePoint(self, point):
        if point in self.points:
            self.points.remove(point)
            self.calcBoundingBox()

    def calcBoundingBox(self):
        self.minX = None
        self.minY = None
        self.minZ = None
        self.maxX = None
        self.maxY = None
        self.maxZ = None
        mins = Point3(99999999)
        maxs = Point3(-99999999)
        for point in self.points:
            if point.x < mins.x:
                mins.x = point.x
            if point.y < mins.y:
                mins.y = point.y
            if point.z < mins.z:
                mins.z = point.z

            if point.x > maxs.x:
                maxs.x = point.x
            if point.y > maxs.y:
                maxs.y = point.y
            if point.z > maxs.z:
                maxs.z = point.z

            if self.minX is None or point.x < self.minX.x:
                self.minX = point
            if self.minY is None or point.y < self.minY.y:
                self.minY = point
            if self.minZ is None or point.z < self.minZ.z:
                self.minZ = point
            if self.maxX is None or point.x > self.maxX.x:
                self.maxX = point
            if self.maxY is None or point.y > self.maxY.y:
                self.maxY = point
            if self.maxZ is None or point.z > self.maxZ.z:
                self.maxZ = point

        self.mins = mins
        self.maxs = maxs

        self.boundingBox = BoundingBox(self.mins, self.maxs)
        self.extents = [
            self.minX, self.minY, self.minZ,
            self.maxX, self.maxY, self.maxZ
        ]
