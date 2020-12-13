from .SelectionMode import SelectionMode
from .SelectionType import SelectionModeTransform, SelectionType
from direct.foundry.KeyBind import KeyBind

from direct.foundry import LEGlobals

class VertexMode(SelectionMode):

    Type = SelectionType.Vertices
    Mask = LEGlobals.FaceMask
    Key = "solidvertex"
    CanDelete = False
    CanDuplicate = False
    TransformBits = SelectionModeTransform.Translate
    KeyBind = KeyBind.SelectVertices
    Icon = "icons/editor-select-verts.png"
    Name = "Vertices"
    Desc = "Select solid vertices"

    def onSelectionsChanged(self):
        pass
