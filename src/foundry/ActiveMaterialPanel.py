from PyQt5 import QtWidgets, QtGui, QtCore

from direct.showbase.DirectObject import DirectObject

from direct.foundry import MaterialPool
from direct.foundry.EditFaceMaterial import EditFaceMaterial
from direct.foundry.ActionGroup import ActionGroup
from direct.foundry.Solid import Solid
from direct.foundry.SolidFace import SolidFace

class ActiveMaterialPanel(QtWidgets.QDockWidget, DirectObject):

    def __init__(self):
        QtWidgets.QDockWidget.__init__(self)
        DirectObject.__init__(self)

        self.setWindowTitle("Active Material")

        container = QtWidgets.QWidget(self)
        container.setLayout(QtWidgets.QVBoxLayout())
        self.setWidget(container)

        self.matIcon = QtWidgets.QLabel("", parent=container)
        self.matIcon.setAlignment(QtCore.Qt.AlignCenter)
        container.layout().addWidget(self.matIcon)

        self.matEdit = QtWidgets.QLineEdit("", container)
        container.layout().addWidget(self.matEdit)

        brContainer = QtWidgets.QWidget(container)
        brContainer.setLayout(QtWidgets.QHBoxLayout())
        brContainer.layout().setContentsMargins(0, 0, 0, 0)
        brContainer.layout().addSpacerItem(
            QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                  QtWidgets.QSizePolicy.Preferred))
        self.matReplace = QtWidgets.QPushButton("Replace...", brContainer)
        brContainer.layout().addWidget(self.matReplace)
        self.matBrowse = QtWidgets.QPushButton("Browse...", brContainer)
        self.matBrowse.clicked.connect(self.__browseForMaterial)
        brContainer.layout().addWidget(self.matBrowse)
        container.layout().addWidget(brContainer)

        self.applyBtn = QtWidgets.QPushButton("Apply Active Material", container)
        self.applyBtn.clicked.connect(self.__applyActiveMaterial)
        container.layout().addWidget(self.applyBtn)

        container.layout().addSpacerItem(
            QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Preferred,
                                  QtWidgets.QSizePolicy.Expanding))

        base.qtWindow.addDockWindow(self, "left")
        self.hide()

        self.accept('activeMaterialChanged', self.updateIcon)

    def __applyActiveMaterial(self):
        if len(base.selectionMgr.selectedObjects) == 0:
            return

        actions = []

        faces = 0

        for obj in base.selectionMgr.selectedObjects:
            if isinstance(obj, Solid):
                # Apply to all faces of solid
                for face in obj.faces:
                    edit = EditFaceMaterial(face)
                    edit.material.material = MaterialPool.ActiveMaterial
                    actions.append(edit)
                    faces += 1
            elif isinstance(obj, SolidFace):
                edit = EditFaceMaterial(obj)
                edit.material.material = MaterialPool.ActiveMaterial
                actions.append(edit)
                faces += 1

        if faces == 0:
            return

        base.actionMgr.performAction("Apply active material to %i face(s)" % faces, ActionGroup(actions))

    def __browseForMaterial(self):
        base.materialBrowser.show(self, self.__materialBrowserDone)

    def __materialBrowserDone(self, status, asset):
        if status:
            MaterialPool.setActiveMaterial(MaterialPool.getMaterial(asset))

    def updateIcon(self, mat = None):
        if not mat:
            mat = MaterialPool.ActiveMaterial

        self.matIcon.setPixmap(MaterialPool.ActiveMaterial.pixmap.scaled(128, 128,
            QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        self.matEdit.setText(MaterialPool.ActiveMaterial.filename.getFullpath())
