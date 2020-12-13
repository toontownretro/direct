from .ObjectMode import ObjectMode
from .SelectionType import SelectionType
from direct.foundry.KeyBind import KeyBind
from direct.foundry.Entity import Entity
from direct.foundry.Group import Group

class GroupsMode(ObjectMode):

    Type = SelectionType.Groups
    KeyBind = KeyBind.SelectGroups
    Icon = "icons/editor-select-groups.png"
    Name = "Groups"
    Desc = "Select object groups"
    ToolOnly = False

    def getActualObject(self, obj, entry):
        # Find the highest non-world parent of the object,
        # and select all of its children.

        top = obj.findTopmostParent((Entity, Group))
        if not top:
            # Object has no parent.
            top = obj

        objects = [top]
        objects += top.findAllChildren()

        return objects

    def getObjectPropertiesTarget(self):
        # Use the most recently selected group.
        # If there's no group, use the most recently selected entity.
        # If there's no entity, use the most recently selected object.
        groups = [o for o in self.mgr.selectedObjects if isinstance(o, Group)]
        entities = [o for o in self.mgr.selectedObjects if isinstance(o, Entity)]
        if len(groups) > 0:
            return groups[len(groups) - 1]
        elif len(entities) > 0:
            return entities[len(entities) - 1]
        else:
            return self.mgr.selectedObjects[len(self.mgr.selectedObjects) - 1]

    def updateModeActions(self):
        ObjectMode.updateModeActions(self)
        if len(self.mgr.selectedObjects) > 1:
            base.menuMgr.enableAction(KeyBind.GroupSelected)
            base.menuMgr.enableAction(KeyBind.UngroupSelected)
        else:
            base.menuMgr.disableAction(KeyBind.GroupSelected)
            base.menuMgr.disableAction(KeyBind.UngroupSelected)

    def activate(self):
        base.menuMgr.connect(KeyBind.GroupSelected, self.__groupSelected)
        base.menuMgr.connect(KeyBind.UngroupSelected, self.__ungroupSelected)
        ObjectMode.activate(self)

    def deactivate(self):
        base.menuMgr.disconnect(KeyBind.GroupSelected, self.__groupSelected)
        base.menuMgr.disconnect(KeyBind.UngroupSelected, self.__ungroupSelected)
        ObjectMode.deactivate(self)

    def __groupSelected(self):
        print("Grouping selected objects")

    def __ungroupSelected(self):
        print("Ungrouping selected objects")
