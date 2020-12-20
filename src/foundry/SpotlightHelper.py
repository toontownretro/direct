from panda3d.core import Spotlight, Vec4, Vec3, CKeyValues, LineSegs, NodePath, deg2Rad, AntialiasAttrib, ShaderParamAttrib

from .MapHelper import MapHelper

from direct.foundry import LEGlobals, LEUtils
from direct.directbase import DirectRender

import math

InnerColor = LEGlobals.vec3GammaToLinear(Vec4(1.0, 1.0, 0, 1))
OuterColor = LEGlobals.vec3GammaToLinear(Vec4(1.0, 0.5, 0, 1))

UnitCone = None
def getUnitCone():
    global UnitCone
    if not UnitCone:
        segs = LineSegs('unitCone')

        dist = 1

        points = [Vec3(-dist, 1, 0),
                  Vec3(0, 1, dist),
                  Vec3(0, 1, -dist),
                  Vec3(dist, 1, 0)]
        for point in points:
            segs.moveTo(Vec3(0))
            segs.drawTo(point)

        vertices = LEUtils.circle(0, 0, dist, 64)
        for i in range(len(vertices)):
            x1, y1 = vertices[i]
            x2, y2 = vertices[(i + 1) % len(vertices)]
            pFrom = Vec3(x1, 1, y1)
            pTo = Vec3(x2, 1, y2)
            segs.moveTo(pFrom)
            segs.drawTo(pTo)

        UnitCone = NodePath(segs.create())
        UnitCone.setAntialias(AntialiasAttrib.MLine)
        UnitCone.setLightOff(1)
        UnitCone.setFogOff(1)
        UnitCone.hide(DirectRender.ShadowCameraBitmask | DirectRender.ReflectionCameraBitmask)

    return UnitCone

class SpotlightHelper(MapHelper):

    ChangeWith = [
        "_light",
        "_intensity",
        "_constant_attn",
        "_linear_attn",
        "_quadratic_attn",
        "_inner_radius",
        "_outer_radius",
        "_inner_cone",
        "_cone",
        "_exponent",
        "_shadow_caster",
        "_depth_bias",
        "_normal_offset_scale",
        "_normal_offset_uv_space",
        "_softness_factor",
        "_shadow_map_size"
    ]

    def __init__(self, mapObject):
        MapHelper.__init__(self, mapObject)
        self.spotlightMdl = None
        self.light = None
        self.innerCone = None
        self.outerCone = None
        self.hasLight = False

    def generate(self, helperInfo):
        color = self.mapObject.getPropertyValue("_light", default = Vec4(255, 255, 255, 255))
        color = LEGlobals.colorFromRGBScalar255(color)
        color = LEGlobals.vec3GammaToLinear(color)

        intensity = self.mapObject.getPropertyValue("_intensity", default = 1.0)
        innerRadius = self.mapObject.getPropertyValue("_inner_radius", default = 1.0)
        outerRadius = self.mapObject.getPropertyValue("_outer_radius", default = 2.0)

        color[0] = color[0] * intensity
        color[1] = color[1] * intensity
        color[2] = color[2] * intensity

        constant = self.mapObject.getPropertyValue("_constant_attn", default = 0.0)
        linear = self.mapObject.getPropertyValue("_linear_attn", default = 0.0)
        quadratic = self.mapObject.getPropertyValue("_quadratic_attn", default = 1.0)

        innerConeDeg = self.mapObject.getPropertyValue("_inner_cone")
        innerConeRad = deg2Rad(innerConeDeg)
        outerConeDeg = self.mapObject.getPropertyValue("_cone")
        outerConeRad = deg2Rad(outerConeDeg)

        depthBias = self.mapObject.getPropertyValue("_depth_bias")
        shadowSize = self.mapObject.getPropertyValue("_shadow_map_size")
        shadowCaster = self.mapObject.getPropertyValue("_shadow_caster")
        softnessFactor = self.mapObject.getPropertyValue("_softness_factor")
        normalOffsetScale = self.mapObject.getPropertyValue("_normal_offset_scale")
        normalOffsetUvSpace = self.mapObject.getPropertyValue("_normal_offset_uv_space")

        pl = Spotlight("lightHelper-light_spot")
        pl.setColor(Vec4(color[0], color[1], color[2], 1.0))
        pl.setFalloff(quadratic)
        pl.setInnerRadius(innerRadius)
        pl.setOuterRadius(outerRadius)
        pl.setExponent(self.mapObject.getPropertyValue("_exponent"))
        pl.setInnerCone(innerConeDeg)
        pl.setOuterCone(outerConeDeg)
        if shadowCaster:
            pl.setCameraMask(DirectRender.ShadowCameraBitmask)
            pl.setShadowCaster(True, shadowSize, shadowSize)
            pl.setDepthBias(depthBias)
            pl.setSoftnessFactor(softnessFactor)
            pl.setNormalOffsetScale(normalOffsetScale)
            pl.setNormalOffsetUvSpace(normalOffsetUvSpace)
        self.light = self.mapObject.helperRoot.attachNewNode(pl)
        if True:#self.mapObject.doc.numlights < 64:
            self.mapObject.doc.render.setLight(self.light)
            self.mapObject.doc.numlights += 1
            self.hasLight = True

        self.spotlightMdl = base.loader.loadModel("models/misc/spotlight-editor.bam")
        #self.spotlightMdl.setState("materials/spotlight-editor.mat")
        #state = self.spotlightMdl.getState()
        #params = state.getAttrib(ShaderParamAttrib)
        #params = params.setParam("selfillumtint", CKeyValues.toString(color.getXyz()))
        #print(params)
        #self.spotlightMdl.setState(state.setAttrib(params))
        self.spotlightMdl.reparentTo(self.light)
        self.spotlightMdl.setScale(0.5)
        self.spotlightMdl.setH(180)
        self.spotlightMdl.setLightOff(1)
        self.spotlightMdl.setRenderModeWireframe(1)
        self.spotlightMdl.setTextureOff(1)
        self.spotlightMdl.setColor(Vec4(0, 0, 0, 1))
        #self.spotlightMdl.setLightOff(self.light, 1)
        #self.spotlightMdl.ls()

        innerCone = getUnitCone().copyTo(self.light)
        innerCone.setSy(innerRadius)
        innerCone.setSx((innerConeRad/2) *innerRadius)
        innerCone.setSz((innerConeRad/2) *innerRadius)
        innerCone.setColorScale(InnerColor)
        self.innerCone = innerCone

        outerCone = getUnitCone().copyTo(self.light)
        outerCone.setSy(outerRadius)
        outerCone.setSx((outerConeRad/2) *outerRadius)
        outerCone.setSz((outerConeRad/2) *outerRadius)
        outerCone.setColorScale(OuterColor)
        self.outerCone = outerCone

        if not self.mapObject.selected:
            innerCone.stash()
            outerCone.stash()

    def disable(self):
        if self.light and self.hasLight:
            self.mapObject.doc.render.clearLight(self.light)

    def unDisable(self):
        if self.light and self.hasLight:
            self.mapObject.doc.render.setLight(self.light)

    def select(self):
        self.innerCone.unstash()
        self.outerCone.unstash()

    def deselect(self):
        self.innerCone.stash()
        self.outerCone.stash()

    def cleanup(self):
        if self.light:
            if self.hasLight:
                self.mapObject.doc.render.clearLight(self.light)
                self.mapObject.doc.numlights -= 1
            self.light.removeNode()
            self.light = None
        self.innerCone = None
        self.outerCone = None
        self.hasLight = None
        MapHelper.cleanup(self)
