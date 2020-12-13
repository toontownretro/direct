from .BrushControl import BrushControl

from PyQt5 import QtWidgets, QtCore

class BooleanControl(BrushControl):

    def __init__(self, brush, label, callback = None, checked = False, enabled = True):
        BrushControl.__init__(self, brush, label, callback)
        self.control = QtWidgets.QCheckBox(label)
        self.control.setChecked(checked)
        self.control.setEnabled(enabled)
        self.control.stateChanged.connect(self.__stateChanged)

    def __stateChanged(self, state):
        self.valueChanged((state == QtCore.Qt.Checked))

    def getValue(self):
        return self.control.isChecked()
