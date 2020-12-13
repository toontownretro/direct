from panda3d.core import PointLight, Vec4, Vec3, CKeyValues

from .MapHelper import MapHelper

from direct.foundry import LEGlobals

class LightHelper(MapHelper):

    ChangeWith = [
        "_light",
        "_constant_attn",
        "_linear_attn",
        "_quadratic_attn"
    ]

    def __init__(self, mapObject):
        MapHelper.__init__(self, mapObject)
        self.light = None
        self.hasLight = False

    def generate(self, helperInfo):
        color = self.mapObject.getPropertyValue("_light", default = Vec4(255, 255, 255, 255))
        color = LEGlobals.colorFromRGBScalar255(color)
        color = LEGlobals.vec3GammaToLinear(color)

        constant = float(self.mapObject.getPropertyValue("_constant_attn", default = "0.0"))
        linear = float(self.mapObject.getPropertyValue("_linear_attn", default = "0.0"))
        quadratic = float(self.mapObject.getPropertyValue("_quadratic_attn", default = "1.0"))

        # Scale intensity for unit 100 distance
        ratio = (constant + 100 * linear + 100 * 100 * quadratic)
        if ratio > 0:
            color *= ratio

        pl = PointLight("lightHelper-light")
        pl.setColor(Vec4(color[0], color[1], color[2], 1.0))
        pl.setAttenuation(Vec3(constant, linear, quadratic))
        self.light = self.mapObject.helperRoot.attachNewNode(pl)
        if self.mapObject.doc.numlights < 128:
            self.mapObject.doc.render.setLight(self.light)
            self.mapObject.doc.numlights += 1
            self.hasLight = True

    def cleanup(self):
        if self.light:
            if self.hasLight:
                self.mapObject.doc.render.clearLight(self.light)
                self.mapObject.doc.numlights -= 1
            self.light.removeNode()
            self.light = None
        self.hasLight = None
        MapHelper.cleanup(self)
