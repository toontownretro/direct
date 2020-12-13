from PyQt5 import QtWidgets

class BrushControl:

    def __init__(self, brush, label, callback = None):
        self.label = None
        self.control = None
        self.brush = brush
        self.callback = callback

    def valueChanged(self, newVal):
        if self.callback:
            self.callback(newVal)
        messenger.send('brushValuesChanged', [self.brush])

    def setEnabled(self, val):
        self.control.setEnabled(val)
        if self.label:
            self.label.setEnabled(val)

    def enable(self):
        self.control.setEnabled(True)
        if self.label:
            self.label.setEnabled(True)

    def disable(self):
        self.control.setEnabled(False)
        if self.label:
            self.label.setEnabled(False)

    def getValue(self):
        return 0

    def isEnabled(self):
        return self.control.enabled()
