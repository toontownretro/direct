from .Action import Action

class Select(Action):

    def __init__(self, objects, exclusive):
        Action.__init__(self)
        self.objects = objects
        self.exclusive = exclusive
        if exclusive:
            self.previousSelections = list(base.selectionMgr.selectedObjects)

    def do(self):
        if self.exclusive:
            base.selectionMgr.multiSelect(self.objects)
        else:
            for obj in self.objects:
                base.selectionMgr.select(obj)
        Action.do(self)

    def undo(self):
        if self.exclusive:
            base.selectionMgr.multiSelect(self.previousSelections)
        else:
            for obj in self.objects:
                base.selectionMgr.deselect(obj)
        Action.undo(self)

    def cleanup(self):
        self.objects = None
        self.exclusive = None
        self.previousSelections = None
        Action.cleanup(self)

    def modifiesState(self):
        return False

class Deselect(Action):

    def __init__(self, objects = [], all = False):
        Action.__init__(self)
        self.objects = objects
        self.all = all
        if all:
            self.previousSelections = list(base.selectionMgr.selectedObjects)

    def do(self):
        if self.all:
            base.selectionMgr.deselectAll()
        else:
            for obj in self.objects:
                base.selectionMgr.deselect(obj)
        Action.do(self)

    def undo(self):
        if self.all:
            base.selectionMgr.multiSelect(self.previousSelections)
        else:
            for obj in self.objects:
                base.selectionMgr.select(obj)
        Action.undo(self)

    def cleanup(self):
        self.objects = None
        self.all = None
        self.previousSelections = None
        Action.cleanup(self)

    def modifiesState(self):
        return False
