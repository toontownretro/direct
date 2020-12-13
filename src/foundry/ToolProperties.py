from PyQt5 import QtWidgets, QtCore

class ToolProperties(QtWidgets.QDockWidget):

    GlobalPtr = None

    @staticmethod
    def getGlobalPtr():
        self = ToolProperties
        if not self.GlobalPtr:
            self.GlobalPtr = ToolProperties()
        return self.GlobalPtr

    def __init__(self):
        QtWidgets.QDockWidget.__init__(self)
        self.setWindowTitle("Tool Properties")

        scrollArea = QtWidgets.QScrollArea(self)
        scrollArea.setWidgetResizable(True)
        self.setWidget(scrollArea)

        self.internalWidget = QtWidgets.QWidget(self)
        self.internalWidget.setLayout(QtWidgets.QVBoxLayout())
        self.internalWidget.layout().addSpacerItem(
            QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Preferred,
                QtWidgets.QSizePolicy.Expanding))
        scrollArea.setWidget(self.internalWidget)

        self.groups = []

        self.setMinimumSize(QtCore.QSize(250, 30))

        base.qtWindow.addDockWindow(self, "left")
        self.show()

    def addGroup(self, group):
        if group in self.groups:
            return

        group.setParent(self.internalWidget)
        self.internalWidget.layout().insertWidget(len(self.groups), group)
        group.show()
        self.groups.append(group)

    def removeGroup(self, group, remove = True):
        if not group in self.groups:
            return
        self.internalWidget.layout().removeWidget(group)
        group.setParent(None)
        group.hide()
        if remove:
            self.groups.remove(group)

    def clear(self):
        for group in self.groups:
            self.removeGroup(group, False)
        self.groups = []
