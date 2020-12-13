from panda3d.core import Point3

from .BaseBrush import BaseBrush

from .NumericControl import NumericControl
from direct.foundry import LEUtils

import math

class PipeBrush(BaseBrush):
    Name = "Pipe"

    def __init__(self):
        BaseBrush.__init__(self)
        self.numSides = self.addControl(NumericControl(self, "Number of sides", val = 8))
        self.wallWidth = self.addControl(NumericControl(self, "Wall width", minVal = 1, maxVal = 1024, val = 32))

    def create(self, generator, mins, maxs, material, roundDecimals, temp = False):
        wallWidth = self.wallWidth.getValue()
        if wallWidth < 1:
            return []
        numSides = self.numSides.getValue()
        if numSides < 3:
            return []

        # Very similar to the cylinder, except that we have multiple solids this time
        width = maxs.x - mins.x
        length = maxs.y - mins.y
        height = maxs.z - mins.z
        center = (maxs + mins) / 2
        majorOut = width / 2
        majorIn = majorOut - wallWidth
        minorOut = length / 2
        minorIn = minorOut - wallWidth
        angle = 2 * math.pi / numSides

        # Calc the X,Y for the inner and outer ellipses
        outer = []
        inner = []
        for i in range(numSides):
            a = i * angle
            x = center.x + majorOut * math.cos(a)
            y = center.y + minorOut * math.sin(a)
            z = mins.z
            outer.append(LEUtils.roundVector(Point3(x, y, z), roundDecimals))
            x = center.x + majorIn * math.cos(a)
            y = center.y + minorIn * math.sin(a)
            inner.append(LEUtils.roundVector(Point3(x, y, z), roundDecimals))

        color = LEUtils.getRandomSolidColor()

        # Create the solids
        solids = []
        z = LEUtils.roundVector(Point3(0, 0, height), roundDecimals)
        for i in range(numSides):
            faces = []
            next = (i + 1) % numSides
            faces.append([ outer[i], outer[i] + z, outer[next] + z, outer[next] ])
            faces.append([ inner[next], inner[next] + z, inner[i] + z, inner[i] ])
            faces.append([ outer[next], outer[next] + z, inner[next] + z, inner[next] ])
            faces.append([ inner[i], inner[i] + z, outer[i] + z, outer[i] ])
            faces.append([ inner[next] + z, outer[next] + z, outer[i] + z, inner[i] + z ])
            faces.append([ inner[i], outer[i], outer[next], inner[next] ])
            solids.append(self.makeSolid(generator, faces, material, temp, color))

        return solids
