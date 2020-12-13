from .BrushControl import BrushControl

from PyQt5 import QtWidgets, QtCore

class TextControl(BrushControl):

    def __init__(self, brush, label, callback = None, text = "", placeholder = ""):
        BrushControl.__init__(self, brush, label, callback)
        self.label = QtWidgets.QLabel(label)
        self.control = QtWidgets.QLineEdit(text)
        self.control.setPlaceholderText(placeholder)
        self.control.textEdited.connect(self.valueChanged)

    def getValue(self):
        return self.control.text()
