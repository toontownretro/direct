from .ObjectProperty import ObjectProperty

from . import MetaData

# Represents a single *entity* property that is specified in an fgd file.
class EntityProperty(ObjectProperty):

    def __init__(self, metaData, mapObject):
        ObjectProperty.__init__(self, mapObject)
        self.metaData = metaData
        self.name = metaData.name
        self.valueType = metaData.value_type

        # Set the default value
        if self.metaData.default_value is None:
            self.defaultValue = MetaData.getDefaultValue(self.valueType)
        else:
            self.defaultValue = self.getUnserializedValue(self.metaData.default_value)

        self.value = self.defaultValue

    def clone(self, mapObject):
        prop = EntityProperty(self.metaData, mapObject)
        self.copyBase(prop)
        prop.metaData = self.metaData
        return prop

    def getDisplayName(self):
        return self.metaData.display_name

    def getDescription(self):
        return self.metaData.description

    def isExplicit(self):
        # Not explicit, this came from the FGD file.
        return False
