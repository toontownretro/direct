from .BaseBrush import BaseBrush

from panda3d.core import Point3

from direct.foundry import LEUtils

class WedgeBrush(BaseBrush):
    Name = "Wedge"

    def create(self, generator, mins, maxs, material, roundDecimals, temp = False):
        center = (mins + maxs) / 2
        # The lower Z plane will be base, the x planes will be triangles
        c1 = LEUtils.roundVector(Point3(mins.x, mins.y, mins.z), roundDecimals)
        c2 = LEUtils.roundVector(Point3(maxs.x, mins.y, mins.z), roundDecimals)
        c3 = LEUtils.roundVector(Point3(maxs.x, maxs.y, mins.z), roundDecimals)
        c4 = LEUtils.roundVector(Point3(mins.x, maxs.y, mins.z), roundDecimals)
        c5 = LEUtils.roundVector(Point3(center.x, mins.y, maxs.z), roundDecimals)
        c6 = LEUtils.roundVector(Point3(center.x, maxs.y, maxs.z), roundDecimals)

        faces = [
            [ c1, c2, c3, c4 ],
            [ c2, c1, c5 ],
            [ c5, c6, c3, c2 ],
            [ c4, c3, c6 ],
            [ c6, c5, c1, c4 ]
        ]

        return [self.makeSolid(generator, faces, material, temp)]
