from .Action import Action

class Reparent(Action):

    def __init__(self, obj, newParent):
        Action.__init__(self)
        self.newParent = newParent

        if isinstance(obj, list):
            self.oldParent = {}
            for o in obj:
                self.oldParent[o] = o.parent
        else:
            self.oldParent = obj.parent

        self.obj = obj

    def modifiesState(self):
        return True

    def do(self):
        Action.do(self)
        if isinstance(self.obj, list):
            for o in self.obj:
                o.reparentTo(self.newParent)
        else:
            self.obj.reparentTo(self.newParent)

    def undo(self):
        Action.undo(self)
        if isinstance(self.obj, list):
            for o in self.obj:
                o.reparentTo(self.oldParent[o])
        else:
            self.obj.reparentTo(self.oldParent)

    def cleanup(self):
        self.newParent = None
        self.oldParent = None
        self.obj = None
        Action.cleanup(self)
