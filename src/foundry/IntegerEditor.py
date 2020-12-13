from .BaseEditor import BaseEditor
from .ScrubSpinBox import IntScrubSpinBox, MinVal, MaxVal

from PyQt5 import QtCore

class IntegerEditor(BaseEditor):

    def __init__(self, parent, item, model):
        BaseEditor.__init__(self, parent, item, model)

        self.spinBox = IntScrubSpinBox(self)
        self.spinBox.setRange(MinVal, MaxVal)
        self.spinBox.valueChanged.connect(self.__valueChanged)
        self.layout().addWidget(self.spinBox)

    def __valueChanged(self, val):
        self.setModelData(self.model, self.item.index())

    def setEditorData(self, index):
        self.spinBox.blockSignals(True)
        self.spinBox.setValue(int(self.getItemData()))
        self.spinBox.blockSignals(False)

    def setModelData(self, model, index):
        model.setData(index, str(self.spinBox.value()), QtCore.Qt.EditRole)
