from direct.foundry import MetaData

# Base class for a property that is assigned to a MapObject.
class ObjectProperty:

    def __init__(self, mapObject):
        self.mapObject = mapObject
        self.value = ""
        self.name = ""
        self.valueType = "string"
        self.defaultValue = ""
        self.group = None
        self.writable = True

    def isWritable(self):
        return self.writable

    def setWritable(self, flag):
        self.writable = flag

    def copyBase(self, other):
        other.value = self.value
        other.name = self.name
        other.valueType = self.valueType
        other.defaultValue = self.defaultValue
        other.group = self.group

    def clone(self, mapObject):
        raise NotImplementedError

    # Returns True if this property is explicit, meaning that it is defined in code
    # and part of the object regardless of the FGD meta data.
    def isExplicit(self):
        return True

    def getDisplayName(self):
        return ""

    def getDescription(self):
        return ""

    def getMinValue(self):
        return None

    def getMaxValue(self):
        return None

    def testMinValue(self, value):
        return True

    def testMaxValue(self, value):
        return True

    def setValue(self, value):
        self.value = value

    def getValue(self):
        return self.value

    def getUnserializedValue(self, string):
        if isinstance(string, self.getNativeType()):
            # Already unserialized
            return string
        func = MetaData.getUnserializeFunc(self.valueType)
        ret = func(string)
        return ret

    def getSerializedValue(self):
        func = MetaData.getSerializeFunc(self.valueType)
        return func(self.getValue())

    def getNativeType(self):
        return MetaData.getNativeType(self.valueType)

    def writeKeyValues(self, kv):
        kv.setKeyValue(self.name, self.getSerializedValue())

    def readKeyValues(self, kv):
        self.value = self.getUnserializedValue(kv.getKeyValue(self.name))
