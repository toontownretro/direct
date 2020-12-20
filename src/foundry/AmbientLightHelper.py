from panda3d.core import AmbientLight, Vec4, Vec3, CKeyValues, LineSegs, Quat, NodePath, AntialiasAttrib

from .MapHelper import MapHelper

from direct.foundry import LEGlobals, LEUtils

class AmbientLightHelper(MapHelper):

    ChangeWith = [
        "_light",
        "_intensity"
    ]

    def __init__(self, mapObject):
        MapHelper.__init__(self, mapObject)
        self.light = None
        self.hasLight = False

    def generate(self, helperInfo):
        color = self.mapObject.getPropertyValue("_light", default = Vec4(255, 255, 255, 255))
        color = LEGlobals.colorFromRGBScalar255(color)
        color = LEGlobals.vec3GammaToLinear(color)

        intensity = self.mapObject.getPropertyValue("_intensity", default = 1.0)

        color[0] = color[0] * intensity
        color[1] = color[1] * intensity
        color[2] = color[2] * intensity

        pl = AmbientLight("lightHelper-ambient-light")
        pl.setColor(Vec4(color[0], color[1], color[2], 1.0))
        self.light = self.mapObject.helperRoot.attachNewNode(pl)
        if True:#self.mapObject.doc.numlights < 128:
            print("HI ambient light")
            self.mapObject.doc.render.setLight(self.light)
            self.mapObject.doc.numlights += 1
            self.hasLight = True

    def disable(self):
        if self.light and self.hasLight:
            self.mapObject.doc.render.clearLight(self.light)

    def unDisable(self):
        if self.light and self.hasLight:
            self.mapObject.doc.render.setLight(self.light)

    def cleanup(self):
        if self.light:
            if self.hasLight:
                self.mapObject.doc.render.clearLight(self.light)
                self.mapObject.doc.numlights -= 1
            self.light.removeNode()
            self.light = None
        self.hasLight = None
        MapHelper.cleanup(self)
