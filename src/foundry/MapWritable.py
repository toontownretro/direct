from direct.foundry.DocObject import DocObject

# Base class for serializable map data
class MapWritable(DocObject):

    ObjectName = "writable"

    def __init__(self, doc):
        DocObject.__init__(self, doc)

    def writeKeyValues(self, keyvalues):
        raise NotImplementedError

    def readKeyValues(self, keyvalues):
        raise NotImplementedError
