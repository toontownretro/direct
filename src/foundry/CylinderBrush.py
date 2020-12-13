from panda3d.core import Point3

from .BaseBrush import BaseBrush

from .NumericControl import NumericControl
from direct.foundry import LEUtils

import math

class CylinderBrush(BaseBrush):
    Name = "Cylinder"

    def __init__(self):
        BaseBrush.__init__(self)
        self.numSides = self.addControl(NumericControl(self, "Number of sides", val = 8))

    def create(self, generator, mins, maxs, material, roundDecimals, temp = False):
        numSides = self.numSides.getValue()
        if numSides < 3:
            return []

        # Cylinders can be elliptical so use both major and minor rather than just the radius
        # NOTE: when a low number (< 10ish) of faces are selected this will cause the cylinder to not touch all edges of the box.
        width = maxs.x - mins.x
        length = maxs.y - mins.y
        height = maxs.z - mins.z
        center = (mins + maxs) / 2
        major = width / 2
        minor = length / 2
        angle = 2 * math.pi / numSides

        # Calculate the X and Y points for the ellipse
        points = []
        for i in range(numSides):
            a = i * angle
            xval = center.x + major * math.cos(a)
            yval = center.y + minor * math.sin(a)
            zval = mins.z
            points.append(LEUtils.roundVector(Point3(xval, yval, zval), roundDecimals))

        faces = []
        z = LEUtils.roundVector(Point3(0, 0, height), roundDecimals)
        for i in range(numSides):
            next = (i + 1) % numSides
            faces.append([points[i], points[i] + z, points[next] + z, points[next]])
        # Add the elliptical top and bottom faces
        faces.append(points)
        faces.append([x + z for x in reversed(points)])

        solid = self.makeSolid(generator, faces, material, temp)
        return [solid]
