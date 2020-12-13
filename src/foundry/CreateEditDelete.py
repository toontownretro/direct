from panda3d.core import NodePath

from .Action import Action

class CreateReference:

    def __init__(self, parentId, mapObject):
        self.parentId = parentId
        self.mapObject = mapObject
        self.isSelected = mapObject.selected

    def cleanup(self):
        self.parentId = None
        self.mapObject = None
        self.isSelected = None

class DeleteReference:

    def __init__(self, mapObject):
        self.isSelected = mapObject.selected
        if mapObject.parent:
            self.parentId = mapObject.parent.id
        else:
            self.parentId = None
        print(self.parentId)
        self.mapObject = mapObject

    def cleanup(self):
        self.isSelected = None
        self.parentId = None
        self.mapObject = None

class CreateEditDelete(Action):

    def __init__(self):
        Action.__init__(self)
        self.createObjects = []
        self.deleteObjects = []
        self.editObjects = []

    def modifiesState(self):
        return True

    def create(self, create):
        self.createObjects.append(create)

    def delete(self, delete):
        self.deleteObjects.append(delete)

    def do(self):
        Action.do(self)

        for delete in reversed(self.deleteObjects):
            if delete.isSelected:
                base.selectionMgr.deselect(delete.mapObject)
            delete.mapObject.reparentTo(NodePath())

        for create in self.createObjects:
            create.mapObject.reparentTo(base.document.world.findChildByID(create.parentId))
            if create.isSelected:
                base.selectionMgr.select(create.mapObject)

    def undo(self):
        Action.undo(self)

        for create in reversed(self.createObjects):
            create.isSelected = create.mapObject.selected
            if create.isSelected:
                base.selectionMgr.deselect(create.mapObject)
            create.mapObject.reparentTo(NodePath())

        for delete in self.deleteObjects:
            if delete.parentId is not None:
                delete.mapObject.reparentTo(base.document.world.findChildByID(delete.parentId))
            else:
                delete.mapObject.reparentTo(base.document.world)
            if delete.isSelected:
                base.selectionMgr.select(delete.mapObject)

    def cleanup(self):
        for delete in self.deleteObjects:
            if self.state == self.Done:
                # If the action was performed, get rid of the
                # deleted objects for good.
                delete.mapObject.delete()
            delete.cleanup()
        self.deleteObjects = None

        for create in self.createObjects:
            if self.state == self.Undone:
                # If the action was reversed, get rid of the
                # created objects for good.
                create.mapObject.delete()
            create.cleanup()
        self.createObjects = None

        self.editObjects = None

        Action.cleanup(self)
