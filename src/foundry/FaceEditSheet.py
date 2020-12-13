from panda3d.core import Filename

from .Ui_FaceEditSheet import Ui_FaceEditSheet
from direct.foundry import MaterialPool
from direct.foundry.PointCloud import PointCloud
from direct.foundry.Align import Align
from direct.foundry.EditFaceMaterial import EditFaceMaterial
from direct.foundry.ActionGroup import ActionGroup

from PyQt5 import QtWidgets, QtCore

class FaceEditSheet(QtWidgets.QGroupBox):

    GlobalPtr = None

    @staticmethod
    def getGlobalPtr():
        self = FaceEditSheet
        if not self.GlobalPtr:
            self.GlobalPtr = FaceEditSheet()
        return self.GlobalPtr

    def __init__(self):
        QtWidgets.QGroupBox.__init__(self)
        self.setTitle("Face Editing")
        ui = Ui_FaceEditSheet()
        ui.setupUi(self)
        self.ui = ui

        self.faces = []
        self.face = None
        self.treatAsOne = False

        self.connectEditSignals()
        self.ui.materialFileEdit.returnPressed.connect(self.__materialFileEdited)
        self.ui.btnBrowse.clicked.connect(self.__browseForMaterial)
        self.ui.btnAlignFace.clicked.connect(self.__alignFace)
        self.ui.btnAlignWorld.clicked.connect(self.__alignWorld)
        self.ui.btnFit.clicked.connect(self.__fitTexture)
        self.ui.btnJustifyBottom.clicked.connect(self.__justifyBottom)
        self.ui.btnJustifyCenter.clicked.connect(self.__justifyCenter)
        self.ui.btnJustifyLeft.clicked.connect(self.__justifyLeft)
        self.ui.btnJustifyRight.clicked.connect(self.__justifyRight)
        self.ui.btnJustifyTop.clicked.connect(self.__justifyTop)
        self.ui.chkTreatAsOne.toggled.connect(self.__toggleTreatAsOne)

        self.hide()

    def faceMaterialChanged(self, face):
        if face == self.face:
            self.updateForSelection()

    def __browseForMaterial(self):
        base.materialBrowser.show(self, self.__materialBrowserDone)

    def __materialBrowserDone(self, status, asset):
        if status:
            path = asset.getFullpath()
            self.ui.materialFileEdit.setText(path)
            self.__changeMaterial(path)

    def __getPointCloud(self, faces):
        points = []
        for face in faces:
            for vertex in face.vertices:
                points.append(vertex.getWorldPos())
        return PointCloud(points)

    def __fitTexture(self):
        actions = []

        if self.treatAsOne:
            cloud = self.__getPointCloud(self.faces)
            for face in self.faces:
                action = EditFaceMaterial(face)
                action.material.fitTextureToPointCloud(cloud, 1, 1)
                actions.append(action)
        else:
            for face in self.faces:
                cloud = self.__getPointCloud([face])
                action = EditFaceMaterial(face)
                action.material.fitTextureToPointCloud(cloud, 1, 1)
                actions.append(action)

        base.actionMgr.performAction("Fit texture", ActionGroup(actions))

    def __doAlign(self, mode):
        actions = []

        if self.treatAsOne:
            cloud = self.__getPointCloud(self.faces)
            for face in self.faces:
                action = EditFaceMaterial(face)
                action.material.alignTextureWithPointCloud(cloud, mode)
                actions.append(action)
        else:
            for face in self.faces:
                cloud = self.__getPointCloud([face])
                action = EditFaceMaterial(face)
                action.material.alignTextureWithPointCloud(cloud, mode)
                actions.append(action)

        base.actionMgr.performAction("Align texture %s" % mode.name, ActionGroup(actions))

    def __justifyBottom(self):
        self.__doAlign(Align.Bottom)

    def __justifyCenter(self):
        self.__doAlign(Align.Center)

    def __justifyLeft(self):
        self.__doAlign(Align.Left)

    def __justifyRight(self):
        self.__doAlign(Align.Right)

    def __justifyTop(self):
        self.__doAlign(Align.Top)

    def __toggleTreatAsOne(self, checkState):
        self.treatAsOne = checkState

    def __alignWorld(self):
        actions = []
        for face in self.faces:
            action = EditFaceMaterial(face)
            action.material.alignTextureToWorld(face)
            actions.append(action)
        base.actionMgr.performAction("Align texture to world", ActionGroup(actions))

        self.updateForSelection()

    def __alignFace(self):
        actions = []
        for face in self.faces:
            action = EditFaceMaterial(face)
            action.material.alignTextureToFace(face)
            actions.append(action)
        base.actionMgr.performAction("Align texture to face", ActionGroup(actions))

        self.updateForSelection()

    def updateMaterialIcon(self):
        if self.face:
            self.ui.materialIcon.setPixmap(self.face.material.material.pixmap.scaled(128, 128,
                QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))

    def __materialFileEdited(self):
        filename = self.ui.materialFileEdit.text()
        self.__changeMaterial(filename)

    def __changeMaterial(self, filename):
        actions = []

        mat = MaterialPool.getMaterial(filename)
        MaterialPool.setActiveMaterial(mat)
        for face in self.faces:
            action = EditFaceMaterial(face)
            action.material.material = mat
            actions.append(action)

        base.actionMgr.performAction("Change face material", ActionGroup(actions))

        self.updateMaterialIcon()

    def __xScaleChanged(self, val):
        actions = []
        for face in self.faces:
            action = EditFaceMaterial(face)
            action.material.scale.x = val
            actions.append(action)

        base.actionMgr.performAction("Texture X scale", ActionGroup(actions))

    def __yScaleChanged(self, val):
        actions = []
        for face in self.faces:
            action = EditFaceMaterial(face)
            action.material.scale.y = val
            actions.append(action)

        base.actionMgr.performAction("Texture Y scale", ActionGroup(actions))

    def __xShiftChanged(self, val):
        actions = []
        for face in self.faces:
            action = EditFaceMaterial(face)
            action.material.shift.x = val
            actions.append(action)

        base.actionMgr.performAction("Texture X shift", ActionGroup(actions))

    def __yShiftChanged(self, val):
        actions = []
        for face in self.faces:
            action = EditFaceMaterial(face)
            action.material.shift.x = val
            actions.append(action)

        base.actionMgr.performAction("Texture Y shift", ActionGroup(actions))

    def __rotationChanged(self, val):
        actions = []
        for face in self.faces:
            action = EditFaceMaterial(face)
            action.material.setTextureRotation(val)
            actions.append(action)

        base.actionMgr.performAction("Texture rotation", ActionGroup(actions))

    def connectEditSignals(self):
        self.ui.textureScaleXSpin.valueChanged.connect(self.__xScaleChanged)
        self.ui.textureScaleYSpin.valueChanged.connect(self.__yScaleChanged)
        self.ui.textureShiftXSpin.valueChanged.connect(self.__xShiftChanged)
        self.ui.textureShiftYSpin.valueChanged.connect(self.__yShiftChanged)
        self.ui.rotationSpin.valueChanged.connect(self.__rotationChanged)

    def disconnectEditSignals(self):
        self.ui.textureScaleXSpin.valueChanged.disconnect(self.__xScaleChanged)
        self.ui.textureScaleYSpin.valueChanged.disconnect(self.__yScaleChanged)
        self.ui.textureShiftXSpin.valueChanged.disconnect(self.__xShiftChanged)
        self.ui.textureShiftYSpin.valueChanged.disconnect(self.__yShiftChanged)
        self.ui.rotationSpin.valueChanged.disconnect(self.__rotationChanged)

    def updateForSelection(self):
        if base.selectionMgr.getNumSelectedObjects() == 0:
            self.setEnabled(False)
            return
        else:
            self.setEnabled(True)

        self.faces = []

        faces = list(base.selectionMgr.selectedObjects)
        numFaces = len(faces)
        face = faces[numFaces - 1]

        self.disconnectEditSignals()

        self.ui.textureScaleXSpin.setValue(face.material.scale.x)
        self.ui.textureScaleYSpin.setValue(face.material.scale.y)

        self.ui.textureShiftXSpin.setValue(face.material.shift.x)
        self.ui.textureShiftYSpin.setValue(face.material.shift.y)

        self.ui.rotationSpin.setValue(face.material.rotation)

        self.ui.materialFileEdit.setText(face.material.material.filename.getFullpath())

        self.connectEditSignals()

        self.face = face
        self.faces = faces

        MaterialPool.setActiveMaterial(self.face.material.material)

        self.updateMaterialIcon()
