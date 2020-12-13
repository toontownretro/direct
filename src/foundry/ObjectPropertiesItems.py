from PyQt5 import QtGui, QtCore

from direct.foundry import LEUtils
from direct.foundry.EditObjectProperties import EditObjectProperties

class ObjectPropertiesNullItem(QtGui.QStandardItem):

    def __init__(self, text = ""):
        QtGui.QStandardItem.__init__(self)
        self.setEditable(False)
        self.setText(text)

    def data(self, role):
        if role == QtCore.Qt.SizeHintRole:
            return QtCore.QSize(70, 25)
        return QtGui.QStandardItem.data(self, role)

class ObjectPropertiesItem(QtGui.QStandardItem):

    def __init__(self, win, entity, propName, isKey):
        QtGui.QStandardItem.__init__(self)
        self.win = win
        self.entity = entity
        self.pairing = None
        self.propName = propName
        self.prop = entity.getProperty(propName)
        self.propType = self.prop.valueType
        self.isKey = isKey

        if self.isKey:
            self.setEditable(False)
            self.setText(self.getKeyText())
            self.setToolTip(self.text())
        else:
            self.setEditable(True)
            self.setText(self.computeValueText())

    def setData(self, strData, role, fromUserEdit = True):
        if fromUserEdit and not self.isKey and role == QtCore.Qt.EditRole:
            # Property value was changed... apply it to all the applicable entities

            if self.prop.valueType == "choices":
                # Find the numerical value for the selected choice name
                data = None
                for choice in self.prop.choices:
                    if choice.display_name == strData:
                        data = choice.value
                        break
                assert data is not None, "Could not match %s to a choice value" % strData
            else:
                data = strData

            action = EditObjectProperties(self.entity, {self.propName: data})
            base.actionMgr.performAction("Edit object properties", action)

        QtGui.QStandardItem.setData(self, strData, role)

    def getKeyText(self):
        return self.prop.getDisplayName()

    def computeValueText(self):
        isChoice = self.prop.valueType == "choices"
        entVal = self.entity.getPropertyValue(self.propName, asString = not isChoice)
        if isChoice:
            entVal = self.prop.metaData.choice_by_value(entVal).display_name
        else:
            entVal = str(entVal)
        return entVal

    def data(self, role):
        if role == QtCore.Qt.TextAlignmentRole:
            return QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
        elif role == QtCore.Qt.SizeHintRole:
            return QtCore.QSize(70, 25)
        return QtGui.QStandardItem.data(self, role)

class ObjectPropertiesSpawnflagsItem(ObjectPropertiesItem):

    def __init__(self, win, entity, propName):
        ObjectPropertiesItem.__init__(self, win, entity, propName, True)

        self.flagItems = []

        for flag in self.prop.flagList:
            childKey = ObjectPropertiesFlagItem(self, flag, True)
            childValue = ObjectPropertiesFlagItem(self, flag, False)
            self.appendRow([childKey, childValue])
            self.flagItems.append(childValue)

    def openChildEditors(self):
        for child in self.flagItems:
            self.win.ui.propertiesView.openPersistentEditor(child.index())

    def computeValueText(self):
        for child in self.flagItems:
            child.setText(child.computeValueText())
        return self.prop.name

class ObjectPropertiesFlagItem(QtGui.QStandardItem):

    def __init__(self, flagsItem, spawnFlag, isKey):
        QtGui.QStandardItem.__init__(self)
        self.flagsItem = flagsItem
        self.spawnFlag = spawnFlag
        self.isKey = isKey
        self.propType = "boolean"

        if self.isKey:
            self.setEditable(False)
            self.setText(self.spawnFlag.display_name)
            self.setToolTip(self.text())
        else:
            self.setEditable(True)
            self.setText(self.computeValueText())

    def setData(self, strData, role, fromUserEdit = True):
        if fromUserEdit and not self.isKey and role == QtCore.Qt.EditRole:
            isOn = bool(int(strData))
            if isOn:
                value = self.flagsItem.prop.getValue() | self.spawnFlag.value
            else:
                value = self.flagsItem.prop.getValue() & ~(self.spawnFlag.value)
            action = EditObjectProperties(self.flagsItem.entity, {self.flagsItem.propName: value})
            base.actionMgr.performAction("Edit object spawnflag", action)

        QtGui.QStandardItem.setData(self, strData, role)

    def computeValueText(self):
        return LEUtils.boolToStr(self.flagsItem.prop.hasFlags(self.spawnFlag.value))
