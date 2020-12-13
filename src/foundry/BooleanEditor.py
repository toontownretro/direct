from .BaseEditor import BaseEditor
from PyQt5 import QtWidgets, QtCore

from direct.foundry import LEUtils

class BooleanEditor(BaseEditor):

    def __init__(self, parent, item, model):
        BaseEditor.__init__(self, parent, item, model)
        self.check = QtWidgets.QCheckBox("", self)
        self.check.stateChanged.connect(self.__checkStateChanged)
        self.layout().addWidget(self.check)

    def __checkStateChanged(self, state):
        self.setModelData(self.model, self.item.index())

    def setEditorData(self, index):
        val = LEUtils.strToBool(self.getItemData())
        self.check.blockSignals(True)
        self.check.setChecked(val)
        self.check.blockSignals(False)

    def setModelData(self, model, index):
        model.setData(index, LEUtils.boolToStr(self.check.isChecked()), QtCore.Qt.EditRole)
