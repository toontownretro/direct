from panda3d.core import NodePath, ModelNode, CardMaker, CKeyValues, Vec4
#from panda3d.bsp import BSPMaterial

from direct.foundry import LEGlobals
from direct.foundry.ViewportType import VIEWPORT_3D_MASK

from .MapHelper import MapHelper

class SpriteHelper(MapHelper):

    ChangeWithType = [
        "color255",
        "color1"
    ]

    def __init__(self, mapObject):
        MapHelper.__init__(self, mapObject)
        self.sprite = None

    def generate(self, helperInfo):
        MapHelper.generate(self)

        # Check for a color255 to tint the sprite
        color255Props = self.mapObject.getPropsWithValueType(['color255', 'color1'])
        # If we have a color255 property, select the first one.
        color255Prop = color255Props[0] if len(color255Props) > 0 else None
        if color255Prop:
            color = self.mapObject.getPropertyValue(color255Prop)
            color = LEGlobals.colorFromRGBScalar255(color)
        else:
            color = Vec4(1)

        spritePath = helperInfo['args'][0].replace("\"", "")

        cm = CardMaker("sprite")
        cm.setFrame(-12, 12, -12, 12)
        np = NodePath(cm.generate())
        #np.setBSPMaterial(spritePath)
        np.setColorScale(color)
        np.setLightOff(1)
        np.setFogOff(1)
        np.setBillboardPointEye()
        np.setTransparency(True)
        np.hide(~VIEWPORT_3D_MASK)
        np.reparentTo(self.mapObject.helperRoot)
        self.sprite = np

    def cleanup(self):
        if self.sprite:
            self.sprite.removeNode()
            self.sprite = None
        MapHelper.cleanup(self)
