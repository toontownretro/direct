from panda3d.core import deg2Rad, Point3, Vec3

from .BaseBrush import BaseBrush
import math

from .NumericControl import NumericControl
from .BooleanControl import BooleanControl
from direct.foundry import LEUtils

Atan2 = 63.4

class ArchBrush(BaseBrush):
    Name = "Arch"

    def __init__(self):
        BaseBrush.__init__(self)
        self.numSides = self.addControl(NumericControl(self, "Number of sides", val = 8))
        self.wallWidth = self.addControl(NumericControl(self, "Wall width", minVal = 1, maxVal = 1024, val = 32))
        self.arc = self.addControl(NumericControl(self, "Arc", minVal = 1, maxVal = 360 * 4, val = 360))
        self.startAngle = self.addControl(NumericControl(self, "Start angle", maxVal = 359))
        self.addHeight = self.addControl(NumericControl(self, "Add height", minVal = -1024, maxVal = 1024))
        self.curvedRamp = self.addControl(BooleanControl(self, "Curved ramp", callback = self.__onSetCurvedRamp))
        self.tiltAngle = self.addControl(NumericControl(self, "Tilt angle", minVal = -Atan2, maxVal = Atan2, enabled = False, precision=2))
        self.tiltInterp = self.addControl(BooleanControl(self, "Tilt interpolation", enabled = False))

    def __onSetCurvedRamp(self, val):
        self.tiltAngle.setEnabled(val)
        self.tiltInterp.setEnabled(val)

    def create(self, generator, mins, maxs, material, roundDecimals, temp = False):
        solids = []

        numSides = self.numSides.getValue()
        if numSides < 3:
            return solids
        wallWidth = self.wallWidth.getValue()
        if wallWidth < 1:
            return solids
        arc = self.arc.getValue()
        if arc < 1:
            return solids
        startAngle = self.startAngle.getValue()
        if startAngle < 0 or startAngle > 359:
            return solids
        addHeight = self.addHeight.getValue()
        curvedRamp = self.curvedRamp.getValue()
        tiltAngle = self.tiltAngle.getValue()
        if abs(tiltAngle % 180) == 90:
            return solids
        tiltInterp = curvedRamp and self.tiltInterp.getValue()

        # Very similar to the pipe brush, except with options for start angle, arc, height, and tilt.
        width = maxs.x - mins.x
        length = maxs.y - mins.y
        height = maxs.z - mins.z

        majorOut = width / 2
        majorIn = majorOut - wallWidth
        minorOut = length / 2
        minorIn = minorOut - wallWidth

        start = deg2Rad(startAngle)
        tilt = deg2Rad(tiltAngle)
        angle = deg2Rad(arc) / numSides

        center = (mins + maxs) / 2

        # Calculate the coordinates of the inner and outer ellipses' points.
        outer = []
        inner = []
        for i in range(numSides + 1):
            a = start + i * angle
            h = i * addHeight
            interp = 1
            if tiltInterp:
                interp = math.cos(math.pi / numSides * (i - numSides / 2))
            tiltHeight = wallWidth / 2 * interp * math.tan(tilt)

            xval = center.x + majorOut * math.cos(a)
            yval = center.y + minorOut * math.sin(a)
            zval = mins.z
            if curvedRamp:
                zval += h + tiltHeight
            outer.append(LEUtils.roundVector(Point3(xval, yval, zval), roundDecimals))

            xval = center.x + majorIn * math.cos(a)
            yval = center.y + minorIn * math.sin(a)
            zval = mins.z
            if curvedRamp:
                zval += h - tiltHeight
            inner.append(LEUtils.roundVector(Point3(xval, yval, zval), roundDecimals))

        color = LEUtils.getRandomSolidColor()

        # create the solids
        z = LEUtils.roundVector(Point3(0, 0, height), roundDecimals)
        for i in range(numSides):
            faces = []

            # Since we are triangulating/splitting each arch segment, we need to generate 2 brushes per side
            if curvedRamp:
                # The splitting orientation depends on the curving direction of the arch
                if addHeight >= 0:
                    faces.append([ outer[i],        outer[i] + z,   outer[i+1] + z, outer[i+1] ])
                    faces.append([ outer[i+1],      outer[i+1] + z, inner[i] + z,   inner[i] ])
                    faces.append([ inner[i],        inner[i] + z,   outer[i] + z,   outer[i] ])
                    faces.append([ outer[i] + z,    inner[i] + z,   outer[i+1] + z ])
                    faces.append([ outer[i+1],      inner[i],       outer[i] ])
                else:
                    faces.append([ inner[i+1],      inner[i+1] + z, inner[i] + z,   inner[i] ])
                    faces.append([ outer[i],        outer[i] + z,   inner[i+1] + z, inner[i+1] ])
                    faces.append([ inner[i],        inner[i] + z,   outer[i] + z,   outer[i] ])
                    faces.append([ inner[i+1] + z,  outer[i] + z,   inner[i] + z ])
                    faces.append([ inner[i],        outer[i],       inner[i+1] ])
                solids.append(self.makeSolid(generator, faces, material, temp, color))

                faces.clear()

                if addHeight >= 0:
                    faces.append([ inner[i+1],      inner[i+1] + z, inner[i] + z,   inner[i] ])
                    faces.append([ inner[i],        inner[i] + z,   outer[i+1] + z, outer[i+1] ])
                    faces.append([ outer[i+1],      outer[i+1] + z, inner[i+1] + z, inner[i+1] ])
                    faces.append([ inner[i+1] + z,  outer[i+1] + z, inner[i] + z ])
                    faces.append([ inner[i],        outer[i+1],     inner[i+1] ])
                else:
                    faces.append([ outer[i],        outer[i] + z,   outer[i+1] + z, outer[i+1] ])
                    faces.append([ inner[i+1],      inner[i+1] + z, outer[i] + z,   outer[i] ])
                    faces.append([ outer[i+1],      outer[i+1] + z, inner[i+1] + z, inner[i+1] ])
                    faces.append([ outer[i] + z,    inner[i+1] + z, outer[i+1] + z ])
                    faces.append([ outer[i+1],      inner[i+1],     outer[i] ])

                solids.append(self.makeSolid(generator, faces, material, temp, color))
            else:
                h = Vec3.unitZ() * i * addHeight
                faces.append([ outer[i] + h,    outer[i] + z + h,   outer[i+1] + z + h, outer[i+1] + h ])
                faces.append([ inner[i+1] + h, inner[i+1] + z + h, inner[i] + z + h, inner[i] + h ])
                faces.append([ outer[i+1] + h, outer[i+1] + z + h, inner[i+1] + z + h, inner[i+1] + h])
                faces.append([ inner[i] + h, inner[i] + z + h, outer[i] + z + h, outer[i] + h])
                faces.append([ inner[i+1] + z + h, outer[i+1] + z + h, outer[i] + z + h, inner[i] + z + h ])
                faces.append([ inner[i] + h, outer[i] + h, outer[i+1] + h, inner[i+1] + h ])
                solids.append(self.makeSolid(generator, faces, material, temp, color))

        return solids
