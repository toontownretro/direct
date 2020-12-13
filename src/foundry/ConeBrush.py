from panda3d.core import Point3

from direct.foundry.Plane import Plane

from .BaseBrush import BaseBrush

from .NumericControl import NumericControl
from direct.foundry import LEUtils

import math

class ConeBrush(BaseBrush):

    Name = "Cone"

    def __init__(self):
        BaseBrush.__init__(self)
        self.numSides = self.addControl(NumericControl(self, "Number of sides", val = 8))

    def create(self, generator, mins, maxs, material, roundDecimals, temp = False):
        numSides = self.numSides.getValue()
        if numSides < 3:
            return []

        # This is all very similar to the cylinder brush.
        width = maxs.x - mins.x
        length = maxs.y - mins.y
        center = (mins + maxs) / 2
        major = width / 2
        minor = length / 2
        angle = 2 * math.pi / numSides

        points = []
        for i in range(numSides):
            a = i * angle
            xval = center.x + major * math.cos(a)
            yval = center.y + minor * math.sin(a)
            zval = mins.z
            points.append(LEUtils.roundVector(Point3(xval, yval, zval), roundDecimals))

        faces = []
        point = LEUtils.roundVector(Point3(center.x, center.y, maxs.z), roundDecimals)
        for i in range(numSides):
            next = (i + 1) % numSides
            faces.append([points[i], point, points[next]])
        faces.append(points)

        solid = self.makeSolid(generator, faces, material, temp)
        return [solid]
