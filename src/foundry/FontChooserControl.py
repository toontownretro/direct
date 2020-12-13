from .BrushControl import BrushControl

from PyQt5 import QtWidgets, QtCore

class FontChooserControl(BrushControl):

    def __init__(self, brush, label, callback = None, fontName = ""):
        BrushControl.__init__(self, brush, label, callback)
        self.label = QtWidgets.QLabel(label)
        self.control = QtWidgets.QFontComboBox()
        self.control.currentFontChanged.connect(self.valueChanged)

    def getValue(self):
        return self.control.currentFont()
