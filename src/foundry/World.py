from panda3d.core import CKeyValues

from .Entity import Entity

# The root entity of each map
class World(Entity):

    ObjectName = "world"

    def __init__(self, id):
        Entity.__init__(self, id)
        self.setClassname("worldspawn")
        self.np.node().setFinal(False)

    def doWriteKeyValues(self, parent):
        kv = CKeyValues(self.ObjectName, parent)
        self.writeKeyValues(kv)
        for child in self.children.values():
            if isinstance(child, Entity):
                # Put entities outside of the world key-value block
                par = parent
            else:
                par = kv
            child.doWriteKeyValues(par)
        self.writeEditorValues(kv)

    def isWorld(self):
        return True
