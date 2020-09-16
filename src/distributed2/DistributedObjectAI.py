from .BaseDistributedObject import BaseDistributedObject

# Base server network object
class DistributedObjectAI(BaseDistributedObject):

    def __init__(self):
        BaseDistributedObject.__init__(self)
        self.owner = None

    def delete(self):
        self.owner = None
        BaseDistributedObject.delete(self)
