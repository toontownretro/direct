from .SelectionMode import SelectionMode
from .SelectionType import SelectionType, SelectionModeTransform
from direct.foundry.FaceEditSheet import FaceEditSheet
from direct.foundry import MaterialPool
from direct.foundry.KeyBind import KeyBind
from direct.foundry.EditFaceMaterial import EditFaceMaterial

from direct.foundry import LEGlobals

_FaceEditSheet = None

class FaceMode(SelectionMode):

    Type = SelectionType.Faces
    TransformBits = SelectionModeTransform.Off
    CanDelete = False
    CanDuplicate = False
    Key = "mapobject"
    Mask = LEGlobals.FaceMask
    KeyBind = KeyBind.SelectFaces
    Icon = "icons/editor-select-faces.png"
    Name = "Faces"
    Desc = "Select solid faces"

    def __init__(self, mgr):
        SelectionMode.__init__(self, mgr)
        self.properties = FaceEditSheet.getGlobalPtr()
        self.paintButtonDown = False

    def getActualObject(self, obj, entry):
        return obj.getFaceFromCollisionSolid(entry.getInto())

    def getTranslatedSelections(self, mode):
        if mode in [SelectionType.Groups, SelectionType.Objects]:
            # Select each face of each solid we currently have selected
            faces = []
            for obj in self.mgr.selectedObjects:
                if obj.ObjectName == "solid":
                    faces += obj.faces
            return faces
        else:
            return []

    def toolActivate(self):
        SelectionMode.toolActivate(self)

        self.accept('faceMaterialChanged', self.properties.faceMaterialChanged)
        # Right click on face to apply active material
        # Hold right mouse button and drag to paint active material
        # across faces
        self.accept('mouse3', self.mouse3Down)
        self.accept('mouse3-up', self.mouse3Up)
        self.accept('mouseMoved', self.mouseMove)
        base.materialPanel.hide()
        #self.accept()

    def toolDeactivate(self):
        SelectionMode.toolDeactivate(self)
        base.materialPanel.show()
        self.paintButtonDown = False

    def mouse3Down(self):
        vp = base.viewportMgr.activeViewport
        if not vp.is3D():
            return

        self.paintButtonDown = True
        self.applyActiveMaterial()

    def mouse3Up(self):
        vp = base.viewportMgr.activeViewport
        if not vp.is3D():
            return

        self.paintButtonDown = False

    def mouseMove(self, vp):
        if not vp.is3D():
            return

        if self.paintButtonDown:
            self.applyActiveMaterial()

    def applyActiveMaterial(self):
        objects = self.getObjectsUnderMouse()
        if len(objects) > 0:
            face = objects[0][0]
            if face.material.material != MaterialPool.ActiveMaterial:
                action = EditFaceMaterial(face)
                action.material.material = MaterialPool.ActiveMaterial
                base.actionMgr.performAction("Apply active material", action)
