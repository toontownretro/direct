from PyQt5 import QtWidgets

class ToolOptions(QtWidgets.QWidget):

    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.tool = None

        self.hide()

    def setTool(self, tool):
        self.tool = tool

    def cleanup(self):
        self.tool = None
        self.deleteLater()
