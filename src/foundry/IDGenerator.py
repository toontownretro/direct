from panda3d.core import UniqueIdAllocator

class IDGenerator:

    def __init__(self):
        self.objectId = 0
        self.faceId = 0

    def cleanup(self):
        self.objectId = None
        self.faceId = None

    def reset(self):
        self.objectId = 0
        self.faceId = 0

    def getNextFaceID(self):
        newId = self.faceId
        self.faceId += 1
        return newId

    def reserveFaceID(self, id):
        self.faceId = max(self.faceId, id + 1)

    def getNextID(self):
        newId = self.objectId
        self.objectId += 1
        return newId

    def reserveID(self, id):
        self.objectId = max(self.objectId, id + 1)
