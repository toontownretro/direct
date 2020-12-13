from panda3d.core import Spotlight, Vec4, Vec3, CKeyValues

from .MapHelper import MapHelper

from direct.foundry import LEGlobals

class SpotlightHelper(MapHelper):

    ChangeWith = [
        "_light",
        "_constant_attn",
        "_linear_attn",
        "_quadratic_attn",
        "_cone",
        "_distance",
        "_exponent"
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

        pl = Spotlight("lightHelper-light_spot")
        pl.setColor(Vec4(color[0], color[1], color[2], 1.0))
        pl.setAttenuation(Vec3(constant, linear, quadratic))
        pl.setExponent(self.mapObject.getPropertyValue("_exponent"))
        pl.setMaxDistance(self.mapObject.getPropertyValue("_distance"))
        pl.getLens().setFov(self.mapObject.getPropertyValue("_cone"))
        pl.getLens().setViewHpr(0, -90, 0)
        self.light = self.mapObject.helperRoot.attachNewNode(pl)
        if self.mapObject.doc.numlights < 64:
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
