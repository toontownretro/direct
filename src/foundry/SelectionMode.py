from panda3d.core import CollisionBox, CollisionNode, BitMask32, CollisionHandlerQueue, TransformState, BitMask32

from direct.foundry.DocObject import DocObject
from .SelectionType import SelectionType, SelectionModeTransform

from direct.foundry.KeyBind import KeyBind
from direct.foundry.Line import Line
from direct.foundry.Select import Select, Deselect
from direct.foundry import LEUtils, LEGlobals

class SelectionMode(DocObject):

    Type = SelectionType.Nothing
    # Collision mask used for the mouse click ray
    Mask = 0
    # The key to locate the object from what we clicked on
    Key = None
    # Can we delete the selected objects?
    CanDelete = True
    # Can we clone/duplicate the selected objects?
    CanDuplicate = True
    # What kinds of transform can we apply?
    TransformBits = SelectionModeTransform.All
    ToolOnly = True

    def __init__(self, mgr):
        DocObject.__init__(self, mgr.doc)
        self.mgr = mgr
        self.enabled = False
        self.activated = False
        self.properties = None
        self.entryIdx = 0
        self.lastEntries = None

    def toggleSelect(self, theObj, appendSelect):
        if isinstance(theObj, list):
            obj = theObj[0]
            objs = theObj
        else:
            obj = theObj
            objs = [obj]

        selection = []
        anyAlreadySelected = False
        for o in objs:
            if not self.mgr.isSelected(obj):
                selection.append(o)
            else:
                anyAlreadySelected = True

        if not appendSelect:
            if len(selection) > 0:
                base.actionMgr.performAction("Select %s" % obj.getName(), Select(selection, True))
        else:
            # In multi-select (shift held), if the object we clicked on has
            # already been selected, deselect it.
            if anyAlreadySelected:
                base.actionMgr.performAction("Deselect %s" % obj.getName(), Deselect(objs))
            elif len(selection) > 0:
                base.actionMgr.performAction("Append select %s" % obj.getName(), Select(selection, False))

    def getActualObject(self, obj, entry):
        return obj

    def getObjectsUnderMouse(self):
        vp = base.viewportMgr.activeViewport
        if not vp:
            return []

        entries = vp.click(self.Mask)
        if not entries or len(entries) == 0:
            return []

        objects = []
        key = self.Key
        for i in range(len(entries)):
            # Our entries have been sorted by distance, so use the first (closest) one.
            entry = entries[i]
            np = entry.getIntoNodePath().findNetPythonTag(key)
            if not np.isEmpty():
                # Don't backface cull if there is a billboard effect on or above this node
                if entry.hasSurfaceNormal() and not LEUtils.hasNetBillboard(entry.getIntoNodePath()):
                    surfNorm = entry.getSurfaceNormal(vp.cam).normalized()
                    rayDir = entry.getFrom().getDirection().normalized()
                    if surfNorm.dot(rayDir) >= 0:
                        # Backface cull
                        continue
                obj = np.getPythonTag(key)

                actual = self.getActualObject(obj, entry)
                objects.append((actual, entry))

        return objects

    def cycleNextSelection(self, appendSelect = False):
        if len(self.lastEntries) == 0:
            return

        self.entryIdx = (self.entryIdx + 1) % len(self.lastEntries)
        self.toggleSelect(self.lastEntries[self.entryIdx][0], appendSelect)

    def cyclePreviousSelection(self, appendSelect = False):
        if len(self.lastEntries) == 0:
            return

        self.entryIdx = (self.entryIdx - 1) % len(self.lastEntries)
        self.toggleSelect(self.lastEntries[self.entryIdx][0], appendSelect)

    def selectObjectUnderMouse(self, appendSelect = False):
        objects = self.getObjectsUnderMouse()

        self.lastEntries = objects
        self.entryIdx = 0

        if len(objects) > 0:
            self.toggleSelect(objects[0][0], appendSelect)
            return objects[0][0]

        return None

    def getObjectsInBox(self, mins, maxs):
        objects = []

        # Create a one-off collision box, traverser, and queue to test against all MapObjects
        box = CollisionBox(mins, maxs)
        node = CollisionNode("selectToolCollBox")
        node.addSolid(box)
        node.setFromCollideMask(self.Mask)
        node.setIntoCollideMask(BitMask32.allOff())
        boxNp = self.doc.render.attachNewNode(node)
        queue = CollisionHandlerQueue()
        base.clickTraverse(boxNp, queue)
        queue.sortEntries()
        key = self.Key
        entries = queue.getEntries()
        # Select every MapObject our box intersected with
        for entry in entries:
            np = entry.getIntoNodePath().findNetPythonTag(key)
            if not np.isEmpty():
                obj = np.getPythonTag(key)
                actual = self.getActualObject(obj, entry)
                if isinstance(actual, list):
                    for a in actual:
                        if not any(a == x[0] for x in objects):
                            objects.append((a, entry))
                else:
                    objects.append((actual, entry))
        boxNp.removeNode()

        return objects

    def selectObjectsInBox(self, mins, maxs):
        objects = self.getObjectsInBox(mins, maxs)

        if len(objects) > 0:
            base.actionMgr.performAction("Select %i objects" % len(objects), Select([x[0] for x in objects], True))

    def deselectAll(self):
        self.lastEntries = None
        self.entryIdx = 0

        if base.selectionMgr.hasSelectedObjects():
            base.actionMgr.performAction("Deselect all", Deselect(all = True))

    def deleteSelectedObjects(self):
        base.selectionMgr.deleteSelectedObjects()

    def cleanup(self):
        self.mgr = None
        self.enabled = None
        self.activatated = None
        self.properties = None
        self.lastEntries = None
        self.entryIdx = None
        DocObject.cleanup(self)

    def enable(self):
        self.enabled = True
        self.activate()

    def activate(self):
        self.activated = True
        if not self.ToolOnly:
            self.__activate()

    def disable(self):
        self.enabled = False
        self.toolDeactivate()
        self.deactivate()

    def deactivate(self, docChange = False):
        if not self.ToolOnly:
            self.__deactivate()

    def toolActivate(self):
        if self.ToolOnly:
            self.__activate()

    def toolDeactivate(self):
        if self.ToolOnly:
            self.__deactivate()

    def __activate(self):
        if self.CanDelete:
            base.menuMgr.connect(KeyBind.Delete, self.deleteSelectedObjects)

        self.updateModeActions()

        if self.properties and self.doc.toolMgr:
            base.toolMgr.toolProperties.addGroup(self.properties)
            self.properties.updateForSelection()
        self.accept('selectionsChanged', self.onSelectionsChanged)

    def __deactivate(self):
        if self.CanDelete:
            base.menuMgr.disconnect(KeyBind.Delete, self.deleteSelectedObjects)
        self.activated = False
        self.lastEntries = None
        self.entryIdx = 0
        if self.properties and self.doc.toolMgr:
            base.toolMgr.toolProperties.removeGroup(self.properties)
        self.ignoreAll()

    def updateModeActions(self):
        if self.CanDelete:
            if len(self.mgr.selectedObjects) == 0:
                base.menuMgr.disableAction(KeyBind.Delete)
            else:
                base.menuMgr.enableAction(KeyBind.Delete)

    def onSelectionsChanged(self):
        self.updateModeActions()
        if self.properties:
            self.properties.updateForSelection()

    def getProperties(self):
        return self.properties

    # Returns a list of objects that will be selected
    # when switching to this mode from prevMode.
    def getTranslatedSelections(self, prevMode):
        return []
