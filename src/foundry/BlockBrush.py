from .BaseBrush import BaseBrush

from direct.foundry import LEUtils

class BlockBrush(BaseBrush):
    Name = "Block"

    def create(self, generator, mins, maxs, material, roundDecimals, temp = False):
        faces = LEUtils.getBoxFaces(mins, maxs, roundDecimals)
        return [self.makeSolid(generator, faces, material, temp)]
