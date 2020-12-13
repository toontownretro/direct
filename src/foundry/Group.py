from direct.foundry.MapObject import MapObject

class Group(MapObject):

    def getName(self):
        return "Group of %i objects" % (len(self.children))

    def getDescription(self):
        return ""
