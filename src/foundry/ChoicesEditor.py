from .BaseEditor import BaseEditor

from PyQt5 import QtWidgets, QtCore

class ChoicesEditor(BaseEditor):

    def __init__(self, parent, item, model):
        BaseEditor.__init__(self, parent, item, model)

        self.combo = QtWidgets.QComboBox(self)
        #self.combo.currentIndexChanged.connect(self.__selectedItem)
        self.layout().addWidget(self.combo)

    def __selectedItem(self, index):
        self.setModelData(self.model, self.item.index())

    def setEditorData(self, index):
        self.combo.blockSignals(True)

        self.combo.clear()
        data = self.getItemData()
        prop = self.item.prop
        for choice in prop.metaData.choices:
            self.combo.addItem(choice.display_name)
        self.combo.setCurrentText(data)

        self.combo.blockSignals(False)

    def setModelData(self, model, index):
        model.setData(index, self.combo.currentText(), QtCore.Qt.EditRole)
