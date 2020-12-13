from .BaseBrush import BaseBrush

from .BooleanControl import BooleanControl
from direct.foundry import LEUtils

from panda3d.core import Point3

class TetrahedronBrush(BaseBrush):

    Name = "Tetrahedron"

    def __init__(self):
        BaseBrush.__init__(self)
        self.useCentroid = self.addControl(BooleanControl(self, "Top vertex at centroid"))

    def create(self, generator, mins, maxs, material, roundDecimals, temp = False):
        useCentroid = self.useCentroid.getValue()
        center = (mins + maxs) / 2
        # The lower Z plane will be the triangle, with the lower Y value getting the two corners
        c1 = LEUtils.roundVector(Point3(mins.x, mins.y, mins.z), roundDecimals)
        c2 = LEUtils.roundVector(Point3(maxs.x, mins.y, mins.z), roundDecimals)
        c3 = LEUtils.roundVector(Point3(center.x, maxs.y, mins.z), roundDecimals)
        if useCentroid:
            c4 = Point3((c1.x + c2.x + c3.x) / 3,
                        (c1.y + c2.y + c3.y) / 3,
                        maxs.z)
        else:
            c4 = LEUtils.roundVector(Point3(center.x, center.y, maxs.z), roundDecimals)

        faces = [
            [ c1, c2, c3 ],
            [ c4, c1, c3 ],
            [ c4, c3, c2 ],
            [ c4, c2, c1 ]
        ]

        return [self.makeSolid(generator, faces, material, temp)]
