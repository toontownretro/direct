from PyQt5 import QtWidgets, QtCore

class BaseEditor(QtWidgets.QWidget):

    def __init__(self, parent, item, model):
        QtWidgets.QFrame.__init__(self, parent)
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setAutoFillBackground(True)
        self.item = item
        self.model = model

    def getItemData(self):
        return self.item.data(QtCore.Qt.EditRole)

    def setEditorData(self, index):
        pass

    def setModelData(self, model, index):
        pass
