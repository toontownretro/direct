
from direct.showbase.DirectObject import DirectObject
from direct.directnotify.DirectNotifyGlobal import directNotify

# Base network object class
class BaseDistributedObject(DirectObject):
    notify = directNotify.newCategory("BaseDistributedObject")

    def __init__(self):
        self.doId = None
        self.zoneId = None
        self.dclass = None
        self.generated = False

    def update(self):
        """ Called once per tick to simulate object. """
        pass

    def generate(self):
        self.generated = True

    def delete(self):
        self.ignoreAll()
        self.generated = None
        self.doId = None
        self.zoneId = None
        self.dclass = None
