"""LightingScene module: contains the LightingScene class"""

from panda3d.core import *

from direct.showbase.DirectObject import DirectObject

import math

class LightingScene(DirectObject):
    """
    This class manages the lights within a single scene.
    """

    ShadowBitmask = BitMask32.allOn()

    def __init__(self):
        self.lights = {}

    def __applyLightColor(self, light, color = None, temp = None, intensity = None):
        if color is not None:
            # Assume an explicit color is 0-255 gamma space.
            light.setColor(
                VBase4(
                    math.pow(color[0] / 255, 2.2),
                    math.pow(color[1] / 255, 2.2),
                    math.pow(color[2] / 255, 2.2),
                    1.0))
        elif temp is not None:
            light.setColorTemperature(temp)
        if intensity is not None:
            light.setColor(VBase4(light.getColor().getXyz() * intensity, 1.0))

    def addAmbientLight(self, name, color = None, temp = None, intensity = None):
        light = AmbientLight(name)
        self.__applyLightColor(light, color, temp, intensity)
        lightNp = base.render.attachNewNode(light)
        self.lights[name] = lightNp
        return lightNp

    def addSpotlight(self, name, color = None, temp = None, intensity = None,
                     innerRadius = None, outerRadius = None, innerCone = None,
                     outerCone = None, exponent = None, falloff = None,
                     pos = None, hpr = None, shadows = False, shadowSize = 1024):
        light = Spotlight(name)
        self.__applyLightColor(light, color, temp, intensity)
        if innerRadius is not None:
            light.setInnerRadius(innerRadius)
        if outerRadius is not None:
            light.setOuterRadius(outerRadius)
        if innerCone is not None:
            light.setInnerCone(innerCone)
        if outerCone is not None:
            light.setOuterCone(outerCone)
        if exponent is not None:
            light.setExponent(exponent)
        if falloff is not None:
            light.setFalloff(falloff)
        if shadows:
            light.setShadowCaster(True, shadowSize, shadowSize)
            light.setCameraMask(LightingScene.ShadowBitmask)
        lightNp = base.render.attachNewNode(light)
        if pos is not None:
            lightNp.setPos(pos)
        if hpr is not None:
            lightNp.setHpr(hpr)
        self.lights[name] = lightNp
        return lightNp

    def addPointLight(self, name, color = None, temp = None, intensity = None,
                      innerRadius = None, outerRadius = None, falloff = None,
                      pos = None, hpr = None, shadows = False, shadowSize = 1024):
        light = PointLight(name)
        self.__applyLightColor(light, color, temp, intensity)
        if innerRadius is not None:
            light.setInnerRadius(innerRadius)
        if outerRadius is not None:
            light.setOuterRadius(outerRadius)
        if falloff is not None:
            light.setFalloff(falloff)
        if shadows:
            light.setShadowCaster(True, shadowSize, shadowSize)
            light.setCameraMask(LightingScene.ShadowBitmask)
        lightNp = base.render.attachNewNode(light)
        if pos is not None:
            lightNp.setPos(pos)
        if hpr is not None:
            lightNp.setHpr(hpr)
        self.lights[name] = lightNp
        return lightNp

    def addSunLight(self, name, color = None, temp = None, intensity = None,
                    hpr = None, shadows = False, shadowSize = 4096):
        light = CascadeLight(name)
        self.__applyLightColor(light, color, temp, intensity)
        if shadows:
            light.setShadowCaster(True, shadowSize, shadowSize)
            light.setSceneCamera(base.cam)
            light.setCameraMask(LightingScene.ShadowBitmask)
        lightNp = base.render.attachNewNode(light)
        if hpr is not None:
            lightNp.setHpr(hpr)
        self.lights[name] = lightNp
        return lightNp

    def turnOnLights(self):
        for lightNp in list(self.lights.values()):
            print("Set light", lightNp)
            base.render.setLight(lightNp)

    def turnOnLight(self, name):
        lightNp = self.lights.get(name)
        if lightNp:
            base.render.setLight(lightNp)

    def turnOffLights(self):
        for lightNp in list(self.lights.values()):
            base.render.clearLight(lightNp)

    def turnOffLight(self, name):
        lightNp = self.lights.get(name)
        if lightNp:
            base.render.clearLight(lightNp)

    def removeLight(self, name):
        lightNp = self.lights.get(name)
        if lightNp:
            base.render.clearLight(lightNp)
            lightNp.removeNode()
            del self.lights[name]

    def getLight(self, name):
        return self.lights.get(name)

    def cleanup(self):
        for lightNp in list(self.lights.values()):
            base.render.clearLight(lightNp)
            lightNp.removeNode()
        self.lights = None
