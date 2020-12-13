from .BaseBrush import BaseBrush

from .NumericControl import NumericControl
from direct.foundry import LEUtils

from panda3d.core import Point3, deg2Rad

import math

class SphereBrush(BaseBrush):

    Name = "Sphere"
    CanRound = False

    def __init__(self):
        BaseBrush.__init__(self)
        self.numSides = self.addControl(NumericControl(self, "Number of sides", val = 8))

    def create(self, generator, mins, maxs, material, roundDecimals, temp = False):
        numSides = self.numSides.getValue()
        if numSides < 3:
            return []

        roundDecimals = 2 # Don't support rounding

        width = maxs.x - mins.x
        length = maxs.y - mins.y
        height = maxs.z - mins.z
        center = (maxs + mins) / 2
        major = width / 2
        minor = length / 2
        heightRadius = height / 2

        angleV = deg2Rad(180) / numSides
        angleH = deg2Rad(360) / numSides

        faces = []
        bottom = LEUtils.roundVector(Point3(center.x, center.y, mins.z), roundDecimals)
        top = LEUtils.roundVector(Point3(center.x, center.y, maxs.z), roundDecimals)

        for i in range(numSides):
            # Top -> bottom
            zAngleStart = angleV * i
            zAngleEnd = angleV * (i + 1)
            zStart = heightRadius * math.cos(zAngleStart)
            zEnd = heightRadius * math.cos(zAngleEnd)
            zMultStart = math.sin(zAngleStart)
            zMultEnd = math.sin(zAngleEnd)
            for j in range(numSides):
                # Go around the circle in X/Y
                xyAngleStart = angleH * j
                xyAngleEnd = angleH * ((j + 1) % numSides)
                xyStartX = major * math.cos(xyAngleStart)
                xyStartY = minor * math.sin(xyAngleStart)
                xyEndX = major * math.cos(xyAngleEnd)
                xyEndY = minor * math.sin(xyAngleEnd)
                a = LEUtils.roundVector(Point3(xyStartX * zMultStart, xyStartY * zMultStart, zStart) + center, roundDecimals)
                b = LEUtils.roundVector(Point3(xyEndX * zMultStart, xyEndY * zMultStart, zStart) + center, roundDecimals)
                c = LEUtils.roundVector(Point3(xyEndX * zMultEnd, xyEndY * zMultEnd, zEnd) + center, roundDecimals)
                d = LEUtils.roundVector(Point3(xyStartX * zMultEnd, xyStartY * zMultEnd, zEnd) + center, roundDecimals)

                if i == 0:
                    # Top faces are triangles
                    faces.append([ top, c, d ])
                elif i == (numSides - 1):
                    # Bottom faces are also triangles
                    faces.append([ bottom, a, b ])
                else:
                    # Inner faces are quads
                    faces.append([ a, b, c, d ])

        return [self.makeSolid(generator, faces, material, temp)]
