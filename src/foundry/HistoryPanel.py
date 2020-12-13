from PyQt5 import QtWidgets, QtCore, QtGui

from direct.foundry.DocObject import DocObject

class HistoryPanel(QtWidgets.QDockWidget, DocObject):

    GlobalPtr = None

    @staticmethod
    def getGlobalPtr():
        self = HistoryPanel
        if not self.GlobalPtr:
            self.GlobalPtr = HistoryPanel()
        return self.GlobalPtr

    def __init__(self):
        QtWidgets.QDockWidget.__init__(self)
        self.setWindowTitle("History")

        container = QtWidgets.QWidget(self)
        container.setLayout(QtWidgets.QVBoxLayout())
        container.layout().setContentsMargins(0, 0, 0, 0)
        self.setWidget(container)

        self.actionList = QtWidgets.QListWidget(container)
        self.actionList.itemClicked.connect(self.__onItemClick)
        container.layout().addWidget(self.actionList)

        base.qtWindow.addDockWindow(self, "right")
        self.show()

    def setDoc(self, doc):
        DocObject.setDoc(self, doc)
        self.updateList()

    def __onItemClick(self, item):
        row = self.actionList.row(item)
        index = len(self.doc.actionMgr.history) - row - 1
        self.doc.actionMgr.moveToIndex(index)

    def updateHistoryIndex(self):
        index = self.doc.actionMgr.historyIndex
        if index < 0:
            for i in range(len(self.doc.actionMgr.history)):
                self.actionList.item(i).setSelected(False)
        else:
            row = len(self.doc.actionMgr.history) - index - 1
            self.actionList.item(row).setSelected(True)

        for i in range(len(self.doc.actionMgr.history)):
            row = len(self.doc.actionMgr.history) - i - 1
            if i > index:
                self.actionList.item(row).setForeground(QtGui.QColor(128, 128, 128))
            else:
                self.actionList.item(row).setForeground(QtCore.Qt.white)

    def updateList(self):
        self.actionList.clear()
        for i in range(len(self.doc.actionMgr.history)):
            action = self.doc.actionMgr.history[i]
            self.actionList.insertItem(0, action.desc)
        self.updateHistoryIndex()
