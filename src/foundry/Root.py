from panda3d.core import CKeyValues

from .MapObject import MapObject

# The root object of each map
class Root(MapObject):

    def __init__(self):
        MapObject.__init__(self)
        # We are render
        self.np = base.render

    def clear(self):
        # We have to create a copy of our children to iterate through
        # because deleting a child object removes itself from our list of children.
        # Deleting from a list while iterating through it causes problems.
        children = list(self.children.values())
        for child in children:
            base.document.deleteObject(child)

    def doWriteKeyValues(self):
        kv = CKeyValues()
        for child in self.children.values():
            child.doWriteKeyValues(kv)
        return kv
