from .Action import Action

class ChangeSelectionMode(Action):

    def __init__(self, mode):
        Action.__init__(self)
        self.oldMode = base.selectionMgr.selectionMode.Type
        self.mode = mode
        self.previousSelections = list(base.selectionMgr.selectedObjects)

    def do(self):
        Action.do(self)

        if self.mode == self.oldMode:
            return

        oldAction = base.menuMgr.action(base.selectionMgr.selectionModes[self.oldMode].KeyBind)
        oldAction.setChecked(False)
        newAction = base.menuMgr.action(base.selectionMgr.selectionModes[self.mode].KeyBind)
        newAction.setChecked(True)

        translated = base.selectionMgr.selectionModes[self.mode].getTranslatedSelections(self.oldMode)
        base.selectionMgr.setSelectionMode(self.mode)
        base.selectionMgr.multiSelect(translated)

    def undo(self):
        if self.mode != self.oldMode:
            oldAction = base.menuMgr.action(base.selectionMgr.selectionModes[self.oldMode].KeyBind)
            oldAction.setChecked(True)
            newAction = base.menuMgr.action(base.selectionMgr.selectionModes[self.mode].KeyBind)
            newAction.setChecked(False)

            base.selectionMgr.setSelectionMode(self.oldMode)
            base.selectionMgr.multiSelect(self.previousSelections)

        Action.undo(self)

    def cleanup(self):
        self.oldMode = None
        self.mode = None
        self.previousSelections = None
        Action.cleanup(self)

    def modifiesState(self):
        return False
