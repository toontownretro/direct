from .BaseEditor import BaseEditor

from PyQt5 import QtWidgets, QtCore

class StringEditor(BaseEditor):

    def __init__(self, parent, item, model):
        BaseEditor.__init__(self, parent, item, model)
        self.lineEdit = QtWidgets.QLineEdit(self)
        self.layout().addWidget(self.lineEdit)

    def setEditorData(self, index):
        self.lineEdit.setText(self.getItemData())

    def setModelData(self, model, index):
        model.setData(index, self.lineEdit.text(), QtCore.Qt.EditRole)
