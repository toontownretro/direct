from panda3d.core import Vec3, BitMask32
VIEWPORT_3D         = 0
VIEWPORT_2D_FRONT   = 6
VIEWPORT_2D_SIDE    = 7
VIEWPORT_2D_TOP     = 8

VIEWPORT_3D_MASK = BitMask32.bit(VIEWPORT_3D)
VIEWPORT_2D_MASK = BitMask32.bit(VIEWPORT_2D_FRONT) | \
    BitMask32.bit(VIEWPORT_2D_SIDE) | \
    BitMask32.bit(VIEWPORT_2D_TOP)

class ViewportSpec:
    def __init__(self, type, name):
        self.type = type
        self.name = name

class Viewport2DSpec(ViewportSpec):

    def __init__(self, type, name, unusedCoordinate, viewHpr,
               flattenIndices, expandIndices):
        ViewportSpec.__init__(self, type, name)
        self.unusedCoordinate = unusedCoordinate
        self.viewHpr = viewHpr
        self.flattenIndices = flattenIndices
        self.expandIndices = expandIndices

VIEWPORT_SPECS = {
    VIEWPORT_3D: ViewportSpec(VIEWPORT_3D, "3D Perspective"),
    VIEWPORT_2D_FRONT: Viewport2DSpec(VIEWPORT_2D_FRONT, "2D Front (Y/Z)",
                                      0, Vec3(90, 0, 0), (1, 2),
                                      (-1, 0, 2)),
    VIEWPORT_2D_SIDE: Viewport2DSpec(VIEWPORT_2D_SIDE, "2D Side (X/Z)",
                                     1, Vec3(0, 0, 0), (0, 2),
                                     (0, -1, 2)),
    VIEWPORT_2D_TOP: Viewport2DSpec(VIEWPORT_2D_TOP, "2D Top (X/Y)",
                                    2, Vec3(0, -90, 0), (0, 1),
                                    (0, 2, -1))
}
