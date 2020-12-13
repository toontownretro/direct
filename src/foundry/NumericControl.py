from PyQt5 import QtWidgets
from .BrushControl import BrushControl

class NumericControl(BrushControl):

    def __init__(self, brush, label, callback = None, minVal = 0, maxVal = 99,
                 val = 0, precision = 1, increment = 1, enabled = True):
        BrushControl.__init__(self, brush, label, callback)
        self.label = QtWidgets.QLabel(label)
        if precision > 1:
            self.control = QtWidgets.QDoubleSpinBox()
            self.control.setDecimals(precision)
        else:
            self.control = QtWidgets.QSpinBox()
        self.control.setKeyboardTracking(False)
        self.control.setMinimum(minVal)
        self.control.setMaximum(maxVal)
        self.control.setValue(val)
        self.control.setSingleStep(increment)
        self.control.setEnabled(enabled)

        self.control.valueChanged.connect(self.valueChanged)

    def getValue(self):
        return self.control.value()
