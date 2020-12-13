from .Grid import Grid
from .GridSettings import GridSettings

class Grid2D(Grid):

    def calcZoom(self):
        return self.viewport.zoom * 3

    def shouldRender(self):
        return GridSettings.EnableGrid
