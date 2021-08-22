from panda3d.core import NodePath, CollisionBox, CollisionNode, Vec4, ModelNode, BoundingBox, Vec3
from panda3d.core import Point3, KeyValues, BitMask32, RenderState, ColorAttrib, CullBinAttrib
from panda3d.core import PStatCollector

from .MapWritable import MapWritable
from direct.foundry import LEGlobals
from direct.directbase import DirectRender
from .TransformProperties import OriginProperty, AnglesProperty, ScaleProperty, ShearProperty, TransformProperty
from . import MetaData
from .ObjectProperty import ObjectProperty

from direct.foundry.Line import Line
from direct.foundry.Box import Box
from direct.foundry.GeomView import GeomView
from direct.foundry.ViewportType import VIEWPORT_2D_MASK, VIEWPORT_3D_MASK

from enum import IntEnum

BoundsBox3DState = RenderState.make(
    ColorAttrib.makeFlat(Vec4(1, 1, 0, 1))
)

BoundsBox2DState = RenderState.make(
    ColorAttrib.makeFlat(Vec4(1, 0, 0, 1)),
    CullBinAttrib.make("selected-foreground", 0)
)

MapObjectInit = PStatCollector("Arch:CreateSolid:MapObjInit")

# Base class for any object in the map (brush, entity, etc)
class MapObject(MapWritable):

    ObjectName = "object"

    def __init__(self, id):
        MapObjectInit.start()

        MapWritable.__init__(self, base.document)
        self.temporary = False
        self.id = id
        self.selected = False
        self.classname = ""
        self.parent = None
        self.children = {}
        self.boundingBox = BoundingBox(Vec3(-0.5, -0.5, -0.5), Vec3(0.5, 0.5, 0.5))
        self.boundsBox = Box()
        self.boundsBox.addView(GeomView.Lines, VIEWPORT_3D_MASK, state = BoundsBox3DState)
        self.boundsBox.addView(GeomView.Lines, VIEWPORT_2D_MASK, state = BoundsBox2DState)
        self.boundsBox.generateGeometry()
        self.boundsBox.np.setLightOff(1)
        self.boundsBox.np.setFogOff(1)
        self.boundsBox.np.hide(DirectRender.ShadowCameraBitmask | DirectRender.ReflectionCameraBitmask)
        self.collNp = None

        self.group = None

        self.properties = {}

        # All MapObjects have transform
        self.addProperty(OriginProperty(self))
        self.addProperty(AnglesProperty(self))
        self.addProperty(ScaleProperty(self))
        self.addProperty(ShearProperty(self))

        self.np = NodePath(ModelNode(self.ObjectName + ".%i" % self.id))
        self.np.setPythonTag("mapobject", self)
        self.applyCollideMask()
        # Test bounding volume at this node and but nothing below it.
        self.np.node().setFinal(True)

        MapObjectInit.stop()

    def disable(self):
        pass

    def unDisable(self):
        pass

    def shouldWriteTransform(self):
        return True

    def getClassName(self):
        return self.classname

    def isWorld(self):
        return False

    def r_findAllParents(self, parents, type):
        if not self.parent or self.parent.isWorld():
            return

        if type is None or isinstance(self.parent, type):
            parents.append(self.parent)

        self.parent.r_findAllParents(parents, type)

    def findAllParents(self, type = None):
        parents = []
        self.r_findAllParents(parents, type)
        return parents

    def findTopmostParent(self, type = None):
        parents = self.findAllParents(type)
        if len(parents) == 0:
            return None

        return parents[len(parents) - 1]

    def r_findAllChildren(self, children, type):
        for child in self.children.values():
            if type is None or isinstance(child, type):
                children.append(child)
            child.r_findAllChildren(children, type)

    def findAllChildren(self, type = None):
        children = []

        self.r_findAllChildren(children, type)

        return children

    def applyCollideMask(self):
        self.np.setCollideMask(LEGlobals.ObjectMask)

    def setTemporary(self, flag):
        self.temporary = flag

    # Returns the bounding volume of the object itself, not including children objects.
    def getObjBounds(self, other = None):
        if not other:
            other = self.np.getParent()
        return self.np.getTightBounds(other)

    # Returns the min and max points of the bounds of the object, not including children.
    def getBounds(self, other = None):
        if not other:
            other = self.np.getParent()
        mins = Point3()
        maxs = Point3()
        self.np.calcTightBounds(mins, maxs, other)
        return [mins, maxs]

    def findChildByID(self, id):
        if id == self.id:
            return self

        if id in self.children:
            return self.children[id]

        for child in self.children.values():
            ret = child.findChildByID(id)
            if ret is not None:
                return ret

        return None

    def hasChildWithID(self, id):
        return id in self.children

    def copy(self, generator):
        raise NotImplementedError

    def paste(self, o, generator):
        raise NotImplementedError

    def clone(self):
        raise NotImplementedError

    def unclone(self, o):
        raise NotImplementedError

    #
    # Base copy and paste functions shared by all MapObjects.
    # Each specific MapObject must implement the functions above for their
    # specific functionality.
    #

    def copyProperties(self, props):
        newProps = {}
        for key, prop in props.items():
            newProp = prop.clone(self)
            newProp.setValue(prop.getValue())
            newProps[key] = newProp
        self.updateProperties(newProps)

    def copyBase(self, other, generator, clone = False):
        if clone and other.id != self.id:
            parent = other.parent
            setPar = other.parent is not None and other.parent.hasChildWithID(other.id) and other.parent.children[other.id] == other
            if setPar:
                other.reparentTo(NodePath())
            other.id = self.id
            if setPar:
                other.reparentTo(parent)

        other.parent = self.parent

        for child in self.children.values():
            if clone:
                newChild = child.clone()
            else:
                newChild = child.copy(generator)
            newChild.reparentTo(other)

        other.setClassname(self.classname)
        other.copyProperties(self.properties)
        other.selected = self.selected

    def pasteBase(self, o, generator, performUnclone = False):
        if performUnclone and o.id != self.id:
            parent = self.parent
            setPar = self.parent is not None and self.parent.hasChildWithID(self.id) and self.parent.children[self.id] == self
            if setPar:
                self.reparentTo(NodePath())
            self.id = o.id
            if setPar:
                self.reparentTo(parent)

        for child in o.children.values():
            if performUnclone:
                newChild = child.clone()
            else:
                newChild = child.copy(generator)
            newChild.reparentTo(self)

        self.setClassname(o.classname)
        self.copyProperties(o.properties)
        self.selected = o.selected

    def getName(self):
        return "Object"

    def getDescription(self):
        return "Object in a map."

    def addProperty(self, prop):
        self.properties[prop.name] = prop
        if isinstance(prop, TransformProperty):
            prop.setWritable(self.shouldWriteTransform())

    # Returns list of property names with the specified value types.
    def getPropsWithValueType(self, types):
        if isinstance(types, str):
            types = [types]
        props = []
        for propName, prop in self.properties.items():
            if prop.valueType in types:
                props.append(propName)
        return props

    def getPropNativeType(self, key):
        prop = self.properties.get(key, None)
        if not prop:
            return str

        return prop.getNativeType()

    def getPropValueType(self, key):
        prop = self.properties.get(key, None)
        if not prop:
            return "string"

        return prop.valueType

    def getPropDefaultValue(self, prop):
        if isinstance(prop, str):
            prop = self.properties.get(prop, None)

        if not prop:
            return ""

        return prop.defaultValue

    def getPropertyValue(self, key, asString = False, default = ""):
        prop = self.properties.get(key, None)
        if not prop:
            return default

        if asString:
            return prop.getSerializedValue()
        else:
            return prop.getValue()

    def getProperty(self, name):
        return self.properties.get(name, None)

    def updateProperties(self, data):
        for key, value in data.items():
            if not isinstance(value, ObjectProperty):
                # If only a value was specified and not a property object itself,
                # this is an update to an existing property.

                prop = self.properties.get(key, None)
                if not prop:
                    continue

                oldValue = prop.getValue()

                val = prop.getUnserializedValue(value)

                # If the property has a min/max range, ensure the value we want to
                # set is within that range.
                if (not prop.testMinValue(val)) or (not prop.testMaxValue(val)):
                    # Not within range. Use the default value
                    val = prop.defaultValue

                prop.setValue(val)
            else:
                # A property object was given, simply add it to the dict of properties.
                prop = value
                oldValue = None
                val = prop.getValue()
                self.properties[prop.name] = prop

            self.propertyChanged(prop, oldValue, val)

    def propertyChanged(self, prop, oldValue, newValue):
        if oldValue != newValue:
            self.send('objectPropertyChanged', [self, prop, newValue])

    def setAbsOrigin(self, origin):
        self.np.setPos(base.render, origin)
        self.transformChanged()

    def setOrigin(self, origin):
        self.np.setPos(origin)
        self.transformChanged()

    def getAbsOrigin(self):
        return self.np.getPos(base.render)

    def getOrigin(self):
        return self.np.getPos()

    def setAngles(self, angles):
        self.np.setHpr(angles)
        self.transformChanged()

    def setAbsAngles(self, angles):
        self.np.setHpr(base.render, angles)
        self.transformChanged()

    def getAbsAngles(self):
        return self.np.getHpr(base.render)

    def getAngles(self):
        return self.np.getHpr()

    def setScale(self, scale):
        self.np.setScale(scale)
        self.transformChanged()

    def setAbsScale(self, scale):
        self.np.setScale(base.render, scale)
        self.transformChanged()

    def getAbsScale(self):
        return self.np.getScale(base.render)

    def getScale(self):
        return self.np.getScale()

    def setShear(self, shear):
        self.np.setShear(shear)
        self.transformChanged()

    def setAbsShear(self, shear):
        self.np.setShear(base.render, shear)
        self.transformChanged()

    def getAbsShear(self):
        return self.np.getShear(base.render)

    def getShear(self):
        return self.np.getShear()

    def transformChanged(self):
        self.recalcBoundingBox()
        self.send('objectTransformChanged', [self])

    def showBoundingBox(self):
        self.boundsBox.np.reparentTo(self.np)

    def hideBoundingBox(self):
        self.boundsBox.np.reparentTo(NodePath())

    def select(self):
        self.selected = True
        self.showBoundingBox()
        #self.np.setColorScale(1, 0, 0, 1)

    def deselect(self):
        self.selected = False
        self.hideBoundingBox()
        #self.np.setColorScale(1, 1, 1, 1)

    def setClassname(self, classname):
        self.classname = classname

    def fixBounds(self, mins, maxs):
        # Ensures that the bounds are not flat on any axis
        sameX = mins.x == maxs.x
        sameY = mins.y == maxs.y
        sameZ = mins.z == maxs.z

        invalid = False

        if sameX:
            # Flat horizontal
            if sameY and sameZ:
                invalid = True
            elif not sameY:
                mins.x = mins.y
                maxs.x = maxs.y
            elif not sameZ:
                mins.x = mins.z
                maxs.x = maxs.z

        if sameY:
            # Flat forward/back
            if sameX and sameZ:
                invalid = True
            elif not sameX:
                mins.y = mins.x
                maxs.y = maxs.x
            elif not sameZ:
                mins.y = mins.z
                maxs.y = maxs.z

        if sameZ:
            if sameX and sameY:
                invalid = True
            elif not sameX:
                mins.z = mins.x
                maxs.z = maxs.x
            elif not sameY:
                mins.z = mins.y
                maxs.z = maxs.y

        return [invalid, mins, maxs]

    def recalcBoundingBox(self):
        if not self.np:
            return

        # Don't have the picker box or selection visualization contribute to the
        # calculation of the bounding box.
        if self.collNp:
            self.collNp.stash()
        self.hideBoundingBox()

        # Calculate a bounding box relative to ourself
        mins, maxs = self.getBounds(self.np)

        invalid, mins, maxs = self.fixBounds(mins, maxs)
        if invalid:
            mins = Point3(-0.5)
            maxs = Point3(0.5)

        self.boundingBox = BoundingBox(mins, maxs)
        self.boundsBox.setMinMax(mins, maxs)
        if self.selected:
            self.showBoundingBox()

        if self.collNp:
            self.collNp.unstash()
            self.collNp.node().clearSolids()
            self.collNp.node().addSolid(CollisionBox(mins, maxs))
            self.collNp.hide(~VIEWPORT_3D_MASK)

        self.send('mapObjectBoundsChanged', [self])

    def removePickBox(self):
        if self.collNp:
            self.collNp.removeNode()
            self.collNp = None

    def delete(self):
        if not self.temporary:
            # Take the children with us
            for child in list(self.children.values()):
                child.delete()
            self.children = None
            # if we are selected, deselect
            base.selectionMgr.deselect(self)

        if self.boundsBox:
            self.boundsBox.cleanup()
            self.boundsBox = None

        self.removePickBox()

        if not self.temporary:
            self.reparentTo(NodePath())
        self.np.removeNode()
        self.np = None
        self.properties = None
        self.metaData = None

        self.temporary = None

    def __clearParent(self):
        if self.parent:
            self.parent.__removeChild(self)
            self.np.reparentTo(NodePath())
            self.parent = None

    def __setParent(self, other):
        if isinstance(other, NodePath):
            # We are reparenting directly to a NodePath, outside of the MapObject tree.
            self.parent = None
            self.np.reparentTo(other)
        else:
            self.parent = other
            if self.parent:
                self.parent.__addChild(self)
            self.np.reparentTo(base.render)

    def reparentTo(self, other):
        # If a NodePath is passed to this method, the object will be placed under the specified node
        # in the Panda3D scene graph, but will be taken out of the MapObject tree. If None is passed,
        # the object will be parented to base.render and taken out of the MapObject tree.
        #
        # Use reparentTo(NodePath()) to place the object outside of both the scene graph and the
        # MapObject tree.
        self.__clearParent()
        self.__setParent(other)

    def __addChild(self, child):
        self.children[child.id] = child
        #self.recalcBoundingBox()

    def __removeChild(self, child):
        if child.id in self.children:
            del self.children[child.id]
            #self.recalcBoundingBox()

    def getEditorValues(self):
        return {}

    def readEditorValues(self, kv):
        pass

    def writeEditorValues(self, parent):
        values = self.getEditorValues()
        if len(values) > 0:
            kv = KeyValues("editor", parent)
            for key, value in values.items:
                kv.setKeyValue(key, value)

    def doWriteKeyValues(self, parent):
        kv = KeyValues(self.ObjectName, parent)
        self.writeKeyValues(kv)
        for child in self.children.values():
            child.doWriteKeyValues(kv)
        self.writeEditorValues(kv)

    def writeKeyValues(self, keyvalues):
        keyvalues.setKeyValue("id", str(self.id))
        # Write out our object properties
        for name, prop in self.properties.items():
            if prop.isWritable():
                prop.writeKeyValues(keyvalues)

    def readKeyValues(self, keyvalues):
        for i in range(keyvalues.getNumKeys()):
            key = keyvalues.getKey(i)
            value = keyvalues.getValue(i)
            if MetaData.isPropertyExcluded(key):
                continue
            # Find the property with this name.
            prop = self.properties.get(key, None)
            if not prop:
                # Prop wasn't explicit or part of FGD metadata (if it's an Entity)
                continue

            nativeValue = prop.getUnserializedValue(value)

            # Set the value!
            self.updateProperties({prop.name: nativeValue})
