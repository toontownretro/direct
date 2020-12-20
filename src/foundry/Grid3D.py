from .Grid import Grid
from .GridSettings import GridSettings

from direct.foundry import LEGlobals

class Grid3D(Grid):

    def calcZoom(self):
        z = max(int(abs(self.viewport.camera.getZ() * 16)), 0.001)
        return LEGlobals.clamp(10000 / z, 0.001 * 16, 256 * 16)

    def shouldRender(self):
        return GridSettings.EnableGrid3D
