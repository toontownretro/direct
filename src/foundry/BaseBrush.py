from PyQt5 import QtWidgets

from direct.foundry.Plane import Plane
from direct.foundry.Solid import Solid
from direct.foundry.SolidFace import SolidFace
from direct.foundry.SolidVertex import SolidVertex

from direct.foundry import LEUtils


class BaseBrush:
    Name = "Brush"
    CanRound = True

    def __init__(self):
        self.controls = []
        self.controlsGroup = QtWidgets.QGroupBox(self.Name + " Options")
        self.controlsGroup.setLayout(QtWidgets.QFormLayout())

    def addControl(self, ctrl):
        if ctrl.label:
            self.controlsGroup.layout().addRow(ctrl.label, ctrl.control)
        else:
            self.controlsGroup.layout().addRow(ctrl.control)
        self.controls.append(ctrl)
        return ctrl

    def create(self, generator, mins, maxs, material, roundDecimals, temp = False):
        raise NotImplementedError

    def makeSolid(self, generator, faces, material, temp = False, color = None):
        solid = Solid(generator.getNextID())
        solid.setTemporary(temp)
        if color is not None:
            solid.setColor(color)
        for arr in faces:
            face = SolidFace(generator.getNextFaceID(),
                             Plane.fromVertices(arr[0], arr[1], arr[2]),
                             solid)
            face.setMaterial(material)
            for vert in arr:
                face.vertices.append(SolidVertex(vert, face))
            solid.faces.append(face)
            face.alignTextureToFace()
            if temp:
                face.setPreviewState()
                face.generate()

        if not temp:
            solid.setToSolidOrigin()
            solid.generateFaces()
            solid.recalcBoundingBox()
        else:
            solid.reparentTo(base.render)

        return solid
