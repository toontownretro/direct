from panda3d.core import CascadeLight, Vec4, Vec3, KeyValues, LineSegs, Quat, NodePath, AntialiasAttrib

from .MapHelper import MapHelper

from direct.foundry import LEGlobals, LEUtils
from direct.directbase import DirectRender

class DirLightHelper(MapHelper):

    ChangeWith = [
        "_light",
        "_intensity",
        "_csm_distance",
        "_sun_distance",
        "_csm_log_factor",
        "_csm_border_bias",
        "_csm_fixed_film_size",
        "_num_cascades",
        "_shadow_caster",
        "_depth_bias",
        "_normal_offset_scale",
        "_normal_offset_uv_space",
        "_softness_factor",
        "_shadow_map_size"
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

        csmDistance = self.mapObject.getPropertyValue("_csm_distance")
        sunDistance = self.mapObject.getPropertyValue("_sun_distance")
        csmLogFactor = self.mapObject.getPropertyValue("_csm_log_factor")
        csmBorderBias = self.mapObject.getPropertyValue("_csm_border_bias")
        csmFixedFilmSize = self.mapObject.getPropertyValue("_csm_fixed_film_size")
        numCascades = self.mapObject.getPropertyValue("_num_cascades")
        depthBias = self.mapObject.getPropertyValue("_depth_bias")
        shadowSize = self.mapObject.getPropertyValue("_shadow_map_size")
        shadowCaster = self.mapObject.getPropertyValue("_shadow_caster")
        softnessFactor = self.mapObject.getPropertyValue("_softness_factor")
        normalOffsetScale = self.mapObject.getPropertyValue("_normal_offset_scale")
        normalOffsetUvSpace = self.mapObject.getPropertyValue("_normal_offset_uv_space")

        pl = CascadeLight("lightHelper-light")
        pl.setColor(Vec4(color[0], color[1], color[2], 1.0))
        if shadowCaster:
            pl.setSceneCamera(self.mapObject.doc.get3DViewport().cam)
            pl.setCameraMask(DirectRender.ShadowCameraBitmask)
            pl.setCsmDistance(csmDistance)
            pl.setSunDistance(sunDistance)
            pl.setLogFactor(csmLogFactor)
            pl.setBorderBias(csmBorderBias)
            pl.setUseFixedFilmSize(csmFixedFilmSize)
            pl.setNumCascades(numCascades)
            pl.setDepthBias(depthBias)
            pl.setSoftnessFactor(softnessFactor)
            pl.setNormalOffsetScale(normalOffsetScale)
            pl.setNormalOffsetUvSpace(normalOffsetUvSpace)
            pl.setShadowCaster(True, shadowSize, shadowSize)
        self.light = self.mapObject.helperRoot.attachNewNode(pl)
        if True:#self.mapObject.doc.numlights < 128:
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
