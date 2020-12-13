from panda3d.core import CKeyValues, Vec3, Vec4, Vec2, NodePath

from .MapObject import MapObject
from direct.foundry import HelperFactory
from direct.fgd import PropertyNotFound
from . import MetaData
from .EntityProperty import EntityProperty
from .EntitySpawnflags import EntitySpawnflags

class Entity(MapObject):

    ObjectName = "entity"

    def __init__(self, id):
        MapObject.__init__(self, id)
        self.metaData = None
        self.helperRoot = self.np.attachNewNode("helpers")
        self.helpers = []

    def copy(self, generator):
        e = Entity(generator.getNextID())
        self.copyBase(e, generator)
        return e

    def paste(self, o, generator):
        self.pasteBase(o, generator)

    def clone(self):
        e = Entity(self.id)
        self.copyBase(e, None, True)
        return e

    def unclone(self, o):
        self.pasteBase(o, None, True)

    def getName(self):
        name = self.classname
        targetname = self.getPropertyValue("targetname")
        if len(targetname) > 0:
            name += " - %s" % targetname
        return name

    def getDescription(self):
        if self.metaData.description is None:
            return ""
        else:
            return self.metaData.description

    def hasSpawnflags(self):
        return len(self.metaData.spawnflags) > 0

    def delete(self):
        self.removeHelpers()
        self.helperRoot.removeNode()
        self.helperRoot = None
        MapObject.delete(self)

    def select(self):
        MapObject.select(self)
        for helper in self.helpers:
            helper.select()

    def deselect(self):
        MapObject.deselect(self)
        for helper in self.helpers:
            helper.deselect()

    def removeHelpers(self):
        for helper in self.helpers:
            helper.cleanup()
        self.helpers = []

    def updateHelpers(self):
        self.removeHelpers()
        self.addHelpersForClass()
        self.recalcBoundingBox()

    def addHelpersForClass(self):
        for helperInfo in self.metaData.definitions:
            helper = HelperFactory.createHelper(helperInfo, self)
            if helper:
                self.helpers.append(helper)
        self.applyCollideMask()

    def propertyChanged(self, prop, oldValue, newValue):
        if oldValue != newValue:
            # Check for any helpers that respond to a change
            # in this property.

            for helper in self.helpers:
                # Does this helper respond to a change in this property by name?
                if prop.name in helper.ChangeWith:
                    self.updateHelpers()
                    break

                # How about if it responds to a change in any property
                # with this type?
                if prop.valueType in helper.ChangeWithType:
                    self.updateHelpers()
                    break

        MapObject.propertyChanged(self, prop, oldValue, newValue)

    def getClassType(self):
        return self.metaData.class_type

    def isSolidEntity(self):
        return self.metaData.class_type == 'SolidClass'

    def isPointEntity(self):
        return self.metaData.class_type == 'PointClass'

    def setClassname(self, classname):
        MapObject.setClassname(self, classname)
        if not self.setupMetaData():
            return
        self.setupEntityData()
        self.updateHelpers()

    def setupMetaData(self):
        try:
            self.metaData = base.fgd.entity_by_name(self.classname)
        except:
            self.setClassname("info_null")
        return True

    def setupEntityData(self):
        if not self.metaData:
            return

        # Prune out all FGD properties that are not part of this meta data
        currData = dict(self.properties)
        for name, prop in currData.items():
            if prop.isExplicit() or not isinstance(prop, EntityProperty):
                continue

            try:
                self.metaData.property_by_name(name)
            except PropertyNotFound:
                del self.properties[name]

        # Clear out spawnflags if we have them
        if "spawnflags" in self.properties:
            del self.properties["spawnflags"]

        # Now add in the default values for FGD properties we don't already have.

        for prop in self.metaData.properties:
            if MetaData.isPropertyExcluded(prop.name) or prop.name in self.properties:
                continue

            # New property
            newProp = EntityProperty(prop, self)
            self.updateProperties({newProp.name: newProp})

        if len(self.metaData.spawnflags) > 0:
            # We have spawnflags, add them
            spawnflags = EntitySpawnflags(self.metaData.spawnflags, self)
            self.updateProperties({spawnflags.name: spawnflags})

    def writeKeyValues(self, kv):
        kv.setKeyValue("classname", self.classname)
        MapObject.writeKeyValues(self, kv)

    def readKeyValues(self, kv):
        self.setClassname(kv.getValue("classname"))
        MapObject.readKeyValues(self, kv)
