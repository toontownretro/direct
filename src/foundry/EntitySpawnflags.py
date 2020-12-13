from .ObjectProperty import ObjectProperty

class EntitySpawnflags(ObjectProperty):

    def __init__(self, listOfFlags, mapObject):
        ObjectProperty.__init__(self, mapObject)

        self.flagList = listOfFlags
        self.name = "spawnflags"
        self.valueType = "flags"
        self.defaultValue = 0

        self.value = 0
        for flag in listOfFlags:
            if flag.default_value:
                self.value |= flag.value

    def clone(self, mapObject):
        flags = EntitySpawnflags(list(self.flagList), mapObject)
        self.copyBase(flags)
        return flags

    def getDisplayName(self):
        return "Spawnflags"

    def getDescription(self):
        return "List of flags set on this entity."

    def isExplicit(self):
        # Not explicit, this came from the FGD file.
        return False

    def hasSpawnflags(self):
        return len(self.flagList) > 0

    def hasFlags(self, flags):
        return (self.value & flags) != 0

    def setFlags(self, flags):
        self.value |= flags

    def clearFlags(self, flags):
        self.value &= ~(flags)

    def writeKeyValues(self, kv):
        kv.setKeyValue(self.name, str(self.value))

    def readKeyValues(self, kv):
        self.value = int(kv.getKeyValue(self.name))
