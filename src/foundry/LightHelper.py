from panda3d.core import PointLight, Vec4, Vec3, KeyValues, LineSegs, Quat, NodePath, AntialiasAttrib

from .MapHelper import MapHelper

from direct.foundry import LEGlobals, LEUtils
from direct.directbase import DirectRender

InnerColor = LEGlobals.vec3GammaToLinear(Vec4(1.0, 1.0, 0, 1))
OuterColor = LEGlobals.vec3GammaToLinear(Vec4(1.0, 0.5, 0, 1))

UnitCircle = None
def getUnitCircle():
    global UnitCircle
    if not UnitCircle:
        segs = LineSegs('unitCircle')
        vertices = LEUtils.circle(0, 0, 1, 64)
        angles = [Vec3(0, 0, 0),
                  Vec3(90, 0, 0),
                  Vec3(0, 90, 0)]
        for angle in angles:
            quat = Quat()
            quat.setHpr(angle)
            for i in range(len(vertices)):
                x1, y1 = vertices[i]
                x2, y2 = vertices[(i + 1) % len(vertices)]
                pFrom = quat.xform(Vec3(x1, 0, y1))
                pTo = quat.xform(Vec3(x2, 0, y2))
                segs.moveTo(pFrom)
                segs.drawTo(pTo)
        UnitCircle = NodePath(segs.create())
        UnitCircle.setAntialias(AntialiasAttrib.MLine)
        UnitCircle.setLightOff(1)
        UnitCircle.setFogOff(1)
        UnitCircle.hide(DirectRender.ShadowCameraBitmask | DirectRender.ReflectionCameraBitmask)
    return UnitCircle

class LightHelper(MapHelper):

    ChangeWith = [
        "_light",
        "_intensity",
        "_constant_attn",
        "_linear_attn",
        "_quadratic_attn",
        "_inner_radius",
        "_outer_radius",
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
        self.outerSphere = None
        self.innerSphere = None
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

        depthBias = self.mapObject.getPropertyValue("_depth_bias")
        shadowSize = self.mapObject.getPropertyValue("_shadow_map_size")
        shadowCaster = self.mapObject.getPropertyValue("_shadow_caster")
        softnessFactor = self.mapObject.getPropertyValue("_softness_factor")
        normalOffsetScale = self.mapObject.getPropertyValue("_normal_offset_scale")
        normalOffsetUvSpace = self.mapObject.getPropertyValue("_normal_offset_uv_space")

        pl = PointLight("lightHelper-light")
        pl.setColor(Vec4(color[0], color[1], color[2], 1.0))
        pl.setFalloff(quadratic)
        pl.setInnerRadius(innerRadius)
        pl.setOuterRadius(outerRadius)
        if shadowCaster:
            pl.setCameraMask(DirectRender.ShadowCameraBitmask)
            pl.setShadowCaster(True, shadowSize, shadowSize)
            pl.setDepthBias(depthBias)
            pl.setSoftnessFactor(softnessFactor)
            pl.setNormalOffsetScale(normalOffsetScale)
            pl.setNormalOffsetUvSpace(normalOffsetUvSpace)
        self.light = self.mapObject.helperRoot.attachNewNode(pl)
        if True:#self.mapObject.doc.numlights < 128:
            self.mapObject.doc.render.setLight(self.light)
            self.mapObject.doc.numlights += 1
            self.hasLight = True

        innerSphere = getUnitCircle().copyTo(self.light)
        innerSphere.setScale(innerRadius)
        innerSphere.setColorScale(InnerColor)
        outerSphere = getUnitCircle().copyTo(self.light)
        outerSphere.setScale(outerRadius)
        outerSphere.setColorScale(OuterColor)

        self.innerSphere = innerSphere
        self.outerSphere = outerSphere

        if not self.mapObject.selected:
            innerSphere.stash()
            outerSphere.stash()

    def disable(self):
        if self.light and self.hasLight:
            self.mapObject.doc.render.clearLight(self.light)

    def unDisable(self):
        if self.light and self.hasLight:
            self.mapObject.doc.render.setLight(self.light)

    def select(self):
        self.innerSphere.unstash()
        self.outerSphere.unstash()

    def deselect(self):
        self.innerSphere.stash()
        self.outerSphere.stash()

    def cleanup(self):
        if self.light:
            if self.hasLight:
                self.mapObject.doc.render.clearLight(self.light)
                self.mapObject.doc.numlights -= 1
            self.light.removeNode()
            self.light = None
        self.outerSphere = None
        self.innerSphere = None
        self.hasLight = None
        MapHelper.cleanup(self)
