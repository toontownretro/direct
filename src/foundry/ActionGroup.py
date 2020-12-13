from .Action import Action

# A group of actions that are performed/reversed together, treated as a single action.
class ActionGroup(Action):

    def __init__(self, actions):
        Action.__init__(self)
        self.actions = actions

    def add(self, action):
        if action not in self.actions:
            self.actions.append(action)

    def remove(self, action):
        if action in self.actions:
            self.actions.remove(action)

    def modifiesState(self):
        for action in self.actions:
            if action.modifiesState():
                return True

        return False

    def cleanup(self):
        for action in self.actions:
            action.cleanup()
        self.actions = None
        Action.cleanup(self)

    def do(self):
        Action.do(self)
        for action in self.actions:
            action.do()

    def undo(self):
        Action.undo(self)
        for action in reversed(self.actions):
            action.undo()
