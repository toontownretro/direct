from .BaseEditor import BaseEditor
from direct.foundry import LEUtils

from PyQt5 import QtWidgets, QtCore

class ColorEditor(BaseEditor):

    def __init__(self, parent, item, model):
        BaseEditor.__init__(self, parent, item, model)
        self.lineEdit = QtWidgets.QLineEdit("", self)
        self.lineEdit.returnPressed.connect(self.__confirmColorText)
        self.layout().addWidget(self.lineEdit)
        self.colorLbl = QtWidgets.QLabel("", self)
        self.colorLbl.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.layout().addWidget(self.colorLbl)
        self.editButton = QtWidgets.QPushButton("Pick Color", self)
        self.editButton.clicked.connect(self.__pickColor)
        self.layout().addWidget(self.editButton)
        self.colorDlg = None

        self.adjustToColor(LEUtils.strToQColor(self.getItemData()))

    def __confirmColorText(self):
        self.setModelData(self.model, self.item.index())
        self.adjustToColor(LEUtils.strToQColor(self.lineEdit.text()))

    def __pickColor(self):
        self.origColor = LEUtils.strToQColor(self.getItemData())

        color = LEUtils.strToQColor(self.getItemData())
        colorDlg = QtWidgets.QColorDialog(color, self)
        colorDlg.setOptions(QtWidgets.QColorDialog.DontUseNativeDialog)
        colorDlg.setModal(True)
        colorDlg.currentColorChanged.connect(self.adjustToColorAndSetData)
        colorDlg.finished.connect(self.__colorDlgFinished)
        colorDlg.open()
        colorDlg.blockSignals(True)
        colorDlg.setCurrentColor(color)
        colorDlg.blockSignals(False)
        self.colorDlg = colorDlg

    def __colorDlgFinished(self, ret):
        if ret:
            color = self.colorDlg.currentColor()
            self.adjustToColorAndSetData(color)
        else:
            self.adjustToColorAndSetData(self.origColor)
        self.colorDlg = None

    def adjustToColorAndSetData(self, color):
        if not color.isValid():
            return
        self.adjustToColor(color)
        self.setModelData(self.model, self.item.index())

    def adjustToColor(self, color):
        self.colorLbl.setStyleSheet("border: 1px solid black; background-color: rgb(%i, %i, %i);" % (color.red(), color.green(), color.blue()))
        vals = self.getItemData().split(' ')
        alpha = vals[3]
        self.lineEdit.setText("%i %i %i %s" % (color.red(), color.green(), color.blue(), alpha))

    def setEditorData(self, index):
        self.lineEdit.setText(self.getItemData())

    def setModelData(self, model, index):
        model.setData(index, self.lineEdit.text(), QtCore.Qt.EditRole)
