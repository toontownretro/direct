from .BaseDistributedObject import BaseDistributedObject

# Base server network object
class DistributedObjectAI(BaseDistributedObject):

    def __init__(self):
        BaseDistributedObject.__init__(self)
        self.owner = None

    def sendUpdate(self, name, args = [], client = None, excludeClients = []):
        """
        Sends a non-stateful event message from one object view to another.
        If client is not None, sends the message to that client's object view.
        """
        base.sv.sendUpdate(self, name, args, client, excludeClients)

    def delete(self):
        self.owner = None
        BaseDistributedObject.delete(self)
