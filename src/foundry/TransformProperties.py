from panda3d.core import Vec3

from .ObjectProperty import ObjectProperty

class TransformProperty(ObjectProperty):

    def __init__(self, mapObject):
        ObjectProperty.__init__(self, mapObject)
        self.valueType = "vec3"
        self.defaultValue = Vec3(0)
        self.value = self.defaultValue
        self.group = "Transform"

class OriginProperty(TransformProperty):

    def __init__(self, mapObject):
        TransformProperty.__init__(self, mapObject)
        self.name = "origin"

    def clone(self, mapObject):
        prop = OriginProperty(mapObject)
        self.copyBase(prop)
        return prop

    def getDisplayName(self):
        return "Origin"

    def getDescription(self):
        return "Translational origin of the object."

    def setValue(self, value):
        TransformProperty.setValue(self, value)
        self.mapObject.setOrigin(value)

    def getValue(self):
        return self.mapObject.getOrigin()

class AnglesProperty(TransformProperty):

    def __init__(self, mapObject):
        TransformProperty.__init__(self, mapObject)
        self.name = "angles"

    def clone(self, mapObject):
        prop = AnglesProperty(mapObject)
        self.copyBase(prop)
        return prop

    def getDisplayName(self):
        return "Angles (Yaw Pitch Roll)"

    def getDescription(self):
        return "Orientation of the object, expressed in yaw/pitch/roll Euler angles."

    def setValue(self, value):
        TransformProperty.setValue(self, value)
        self.mapObject.setAngles(value)

    def getValue(self):
        return self.mapObject.getAngles()

class ScaleProperty(TransformProperty):

    def __init__(self, mapObject):
        TransformProperty.__init__(self, mapObject)
        self.defaultValue = Vec3(1)
        self.name = "scale"

    def clone(self, mapObject):
        prop = ScaleProperty(mapObject)
        self.copyBase(prop)
        return prop

    def getDisplayName(self):
        return "Scale"

    def getDescription(self):
        return "Scale of the object. 0 is invalid"

    def getMinValue(self):
        # We can't have a scale of 0
        return 0.00001

    def testMinValue(self, value):
        minVal = self.getMinValue()
        return value.x >= minVal and value.y >= minVal and value.z >= minVal

    def setValue(self, value):
        TransformProperty.setValue(self, value)
        self.mapObject.setScale(value)

    def getValue(self):
        return self.mapObject.getScale()

class ShearProperty(TransformProperty):

    def __init__(self, mapObject):
        TransformProperty.__init__(self, mapObject)
        self.name = "shear"

    def clone(self, mapObject):
        prop = ShearProperty(mapObject)
        self.copyBase(prop)
        return prop

    def getDisplayName(self):
        return "Shear"

    def getDescription(self):
        return "Shear/skew of the object."

    def setValue(self, value):
        TransformProperty.setValue(self, value)
        self.mapObject.setShear(value)

    def getValue(self):
        return self.mapObject.getShear()
