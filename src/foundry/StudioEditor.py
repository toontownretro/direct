from .BaseEditor import BaseEditor
from direct.foundry.ModelBrowser import ModelBrowser

from PyQt5 import QtWidgets, QtCore

class StudioEditor(BaseEditor):

    def __init__(self, parent, item, model):
        BaseEditor.__init__(self, parent, item, model)
        self.lineEdit = QtWidgets.QLineEdit(self)
        self.layout().addWidget(self.lineEdit)
        self.browseBtn = QtWidgets.QPushButton("Browse", self)
        self.browseBtn.clicked.connect(self.__browseForModel)
        self.layout().addWidget(self.browseBtn)

    def __browseForModel(self):
        base.modelBrowser.show(self, self.__modelBrowserDone)

    def __modelBrowserDone(self, ret, path):
        if ret:
            self.lineEdit.setText(path.getFullpath())
            self.setModelData(self.model, self.item.index())

    def setEditorData(self, index):
        self.lineEdit.setText(self.getItemData())

    def setModelData(self, model, index):
        model.setData(index, self.lineEdit.text(), QtCore.Qt.EditRole)
