from .BaseDistributedObject import BaseDistributedObject

# Base client network object
class DistributedObject(BaseDistributedObject):

    neverDisable = False

    def __init__(self):
        BaseDistributedObject.__init__(self)

    def preDataUpdate(self):
        """
        Override this method to do stuff before a state snapshot is unpacked
        onto the object.
        """
        pass

    def postDataUpdate(self):
        """
        Override this method to do stuff after a state snapshot has been
        unpacked onto the object.
        """
        pass

    def sendUpdate(self, name, args = []):
        """
        Sends a non-stateful event message from one object view to another.
        """
        base.cl.sendUpdate(self, name, args)

    def announceGenerate(self):
        """ Called when the object is coming into existence *after* the
        baseline state has been applied, or when the object was disabled and
        it is coming back. """

        pass

    def disable(self):
        """ Called when the object is being temporarily removed/cached away.
        only clean up logical things and remove it from the scene graph, but
        don't tear anything down, because it might come back later via
        announceGenerate(). """

        self.ignoreAll()
        self.removeAllTasks()
