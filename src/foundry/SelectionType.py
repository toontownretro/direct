from enum import IntEnum

class SelectionType(IntEnum):
    Nothing = -1
    # Select individual MapObjects: entities, solids, etc
    Objects = 0
    # Select groups of MapObjects, i.e. when you click on one MapObject
    # it will select that and everything that it is grouped to.
    Groups = 1
    # Select faces of Solids. This pops up the face edit sheet
    Faces = 2
    # Select vertices of Solids
    Vertices = 3

# What kinds of transform are we allowed to apply to our selected objects?
class SelectionModeTransform(IntEnum):

    Off = 0
    Translate = 1 << 0
    Rotate = 1 << 1
    Scale = 1 << 2
    All = Translate | Rotate | Scale
