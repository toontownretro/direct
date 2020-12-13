from .Action import Action

class EditFaceMaterial(Action):

    def __init__(self, face):
        Action.__init__(self)
        self.face = face
        self.origMaterial = self.face.material
        self.material = self.origMaterial.clone()

    def do(self):
        Action.do(self)
        self.face.setFaceMaterial(self.material)

    def undo(self):
        self.face.setFaceMaterial(self.origMaterial)
        Action.undo(self)

    def cleanup(self):
        self.face = None
        self.origMaterial = None
        self.material = None
        Action.cleanup(self)

    def modifiesState(self):
        return True
