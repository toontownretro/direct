from PyQt5 import QtWidgets, QtCore

MaxVal = 2147483647
MinVal = -2147483648

# Bruh. Qt has separate classes for the int and double spin boxes.
class BaseScrubSpinBox:

    def __init__(self):
        self.isMoving = False
        self.mouseStartPosY = 0
        self.startValue = 0

    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.MiddleButton:
            self.mouseStartPosY = e.pos().y()
            self.startValue = self.value()
            self.isMoving = True
            self.setCursor(QtCore.Qt.SizeVerCursor)

    def mouseMoveEvent(self, e):
        if self.isMoving:
            mult = 0.5
            valueOffset = int((self.mouseStartPosY - e.pos().y()) * mult)
            self.setValue(self.startValue + valueOffset)

    def mouseReleaseEvent(self, e):
        self.isMoving = False
        self.unsetCursor()

class IntScrubSpinBox(QtWidgets.QSpinBox, BaseScrubSpinBox):

    def __init__(self, parent):
        QtWidgets.QSpinBox.__init__(self, parent)
        BaseScrubSpinBox.__init__(self)

    def mousePressEvent(self, e):
        QtWidgets.QSpinBox.mousePressEvent(self, e)
        BaseScrubSpinBox.mousePressEvent(self, e)

    def mouseMoveEvent(self, e):
        QtWidgets.QSpinBox.mouseMoveEvent(self, e)
        BaseScrubSpinBox.mouseMoveEvent(self, e)

    def mouseReleaseEvent(self, e):
        QtWidgets.QSpinBox.mouseReleaseEvent(self, e)
        BaseScrubSpinBox.mouseReleaseEvent(self, e)

class DoubleScrubSpinBox(QtWidgets.QDoubleSpinBox, BaseScrubSpinBox):

    def __init__(self, parent):
        QtWidgets.QDoubleSpinBox.__init__(self, parent)
        BaseScrubSpinBox.__init__(self)

    def mousePressEvent(self, e):
        QtWidgets.QDoubleSpinBox.mousePressEvent(self, e)
        BaseScrubSpinBox.mousePressEvent(self, e)

    def mouseMoveEvent(self, e):
        QtWidgets.QDoubleSpinBox.mouseMoveEvent(self, e)
        BaseScrubSpinBox.mouseMoveEvent(self, e)

    def mouseReleaseEvent(self, e):
        QtWidgets.QDoubleSpinBox.mouseReleaseEvent(self, e)
        BaseScrubSpinBox.mouseReleaseEvent(self, e)
