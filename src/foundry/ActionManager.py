from direct.showbase.DirectObject import DirectObject
from direct.foundry.HistoryPanel import HistoryPanel

class ActionEntry:

    def __init__(self, desc, action):
        self.desc = desc
        self.action = action

    def do(self):
        self.action.do()

    def undo(self):
        self.action.undo()

    def modifiesState(self):
        return self.action.modifiesState()

    def cleanup(self):
        self.action.cleanup()
        self.action = None
        self.desc = None

class ActionManager(DirectObject):

    def __init__(self, doc):
        DirectObject.__init__(self)
        self.doc = doc
        self.historyIndex = -1
        self.savedIndex = -1
        self.stateChangeIndex = -1
        self.history = []
        self.panel = HistoryPanel.getGlobalPtr()

        self.accept('documentActivated', self.__onDocActivated)

    def __onDocActivated(self, doc):
        if doc == self.doc:
            self.panel.setDoc(doc)

    def cleanup(self):
        self.doc = None
        self.historyIndex = None
        self.savedIndex = None
        self.stateChangeIndex = None
        for action in self.history:
            action.cleanup()
        self.history = None

    def getCurrentStateChangeIndex(self):
        if self.historyIndex == -1:
            return -1

        # Search back from the current history index to find the most recent state.
        for i in range(self.historyIndex + 1):
            idx = self.historyIndex - i
            action = self.history[idx]
            if action.modifiesState():
                return idx

        return -1

    def documentSaved(self):
        self.savedIndex = self.stateChangeIndex

    def updateSaveStatus(self):
        if self.stateChangeIndex != self.savedIndex:
            self.doc.markUnsaved()
        else:
            self.doc.markSaved()

    def moveToIndex(self, index):
        if index >= len(self.history) or index < -1 or index == self.historyIndex:
            return

        if self.historyIndex > index:
            for i in range(self.historyIndex - index):
                self.undo(True)
        else:
            for i in range(index - self.historyIndex):
                self.redo(True)

        self.updateSaveStatus()
        base.statusBar.showMessage("Move history index")
        self.panel.updateHistoryIndex()

    def undo(self, bulk = False):
        # Anything to undo?
        if len(self.history) == 0 or self.historyIndex < 0:
            # Nope.
            return

        # Get at the current action and undo it
        action = self.history[self.historyIndex]
        action.undo()
        # Move the history index back
        self.historyIndex -= 1

        if action.modifiesState():
            self.stateChangeIndex = self.getCurrentStateChangeIndex()
            if not bulk:
                self.updateSaveStatus()

        if not bulk:
            base.statusBar.showMessage("Undo %s" % action.desc)
            self.panel.updateHistoryIndex()

    def redo(self, bulk = False):
        # Anything to redo?
        numActions = len(self.history)
        if numActions == 0 or self.historyIndex >= numActions - 1:
            return

        # Redo the next action
        self.historyIndex += 1
        action = self.history[self.historyIndex]
        action.do()

        if action.modifiesState():
            self.stateChangeIndex = self.getCurrentStateChangeIndex()
            if not bulk:
                self.updateSaveStatus()

        if not bulk:
            base.statusBar.showMessage("Redo %s" % action.desc)
            self.panel.updateHistoryIndex()

    def performAction(self, description, action):
        # We are overriding everything after the current history index.
        # If the history index is not at the end of the list,
        # shave off everything from the current index to the end of the list.

        if self.historyIndex < len(self.history) - 1:
            first = self.historyIndex + 1
            last = len(self.history) - 1
            for i in range(first, last):
                other = self.history[i]
                other.cleanup()
            del self.history[first:]

            if self.savedIndex > self.historyIndex:
                # If the saved index is ahead of the history index, the
                # saved index is now invalid since those actions have
                # been deleted.
                self.savedIndex = -1

        action.do()
        self.history.append(ActionEntry(description, action))
        self.historyIndex += 1

        if action.modifiesState():
            self.stateChangeIndex = self.getCurrentStateChangeIndex()
            self.updateSaveStatus()

        base.statusBar.showMessage(description)

        self.panel.updateList()
