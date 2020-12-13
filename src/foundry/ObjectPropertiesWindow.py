from direct.foundry.ObjectPropertiesUI import Ui_ObjectProperties
from direct.foundry.DocObject import DocObject
from .ObjectPropertiesDelegate import ObjectPropertiesDelegate
from .ObjectPropertiesItems import ObjectPropertiesItem, ObjectPropertiesNullItem, ObjectPropertiesSpawnflagsItem
from direct.foundry.Entity import Entity

from PyQt5 import QtGui, QtWidgets, QtCore

class ObjectPropertiesModel(QtGui.QStandardItemModel):

    def __init__(self, win):
        QtGui.QStandardItemModel.__init__(self, 0, 2, win.ui.propertiesView)
        self.setColumnCount(2)
        self.setHeaderData(0, QtCore.Qt.Horizontal, "Property")
        self.setHeaderData(1, QtCore.Qt.Horizontal, "Value")

class ObjectPropertiesWindow(QtWidgets.QDockWidget, DocObject):

    GlobalPtr = None

    @staticmethod
    def getGlobalPtr():
        if not ObjectPropertiesWindow.GlobalPtr:
            ObjectPropertiesWindow.GlobalPtr = ObjectPropertiesWindow()
        return ObjectPropertiesWindow.GlobalPtr

    def __init__(self):
        QtWidgets.QDockWidget.__init__(self)
        DocObject.__init__(self, None)
        self.mgr = None
        self.setWindowTitle("Object Properties")
        w = QtWidgets.QWidget(self)
        self.ui = Ui_ObjectProperties()
        self.ui.setupUi(w)
        self.ui.comboClass.setEditable(True)
        self.setWidget(w)

        self.entity = None

        self.valueItemByPropName = {}

        self.propertiesDelegate = ObjectPropertiesDelegate(self)
        self.propertiesModel = ObjectPropertiesModel(self)
        self.ui.propertiesView.setMouseTracking(True)
        self.ui.propertiesView.setModel(self.propertiesModel)
        self.ui.propertiesView.setItemDelegate(self.propertiesDelegate)
        self.ui.propertiesView.header().setDefaultAlignment(QtCore.Qt.AlignCenter)
        self.ui.propertiesView.clicked.connect(self.__propertyClicked)
        self.ui.lePropertyFilter.textChanged.connect(self.__filterProperties)
        self.ui.comboClass.currentIndexChanged.connect(self.__changeEntityClass)

        self.updateAvailableClasses()

        base.qtWindow.addDockWindow(self, "right")
        self.clearAll()
        self.setEnabled(False)

    def setMgr(self, mgr):
        self.mgr = mgr
        self.setDoc(mgr.doc)
        self.accept('objectPropertyChanged', self.__handleObjectPropertyChanged)

    def __handleObjectPropertyChanged(self, entity, prop, value):
        if entity == self.entity:
            item = self.valueItemByPropName.get(prop.name, None)
            if not item:
                return
            item.setData(item.computeValueText(), QtCore.Qt.EditRole, False)

    def clearAll(self):
        self.ui.lePropertyFilter.clear()
        self.propertiesModel.removeRows(0, self.propertiesModel.rowCount())
        self.ui.lblPropertyDesc.setText("")
        self.ui.lblPropertyName.setText("")
        self.ui.comboClass.setCurrentText("")

    def __changeEntityClass(self, idx):
        if not self.mgr:
            return

        classname = self.ui.comboClass.currentText()
        for ent in self.mgr.selectedObjects:
            ent.setClassname(classname)
        self.updateForSelection()
        self.mgr.updateSelectionBounds()

    def __propertyClicked(self, idx):
        item = self.propertiesModel.itemFromIndex(idx)
        if isinstance(item, ObjectPropertiesItem):
            self.updatePropertyDetailText(item.prop)

    def updatePropertyDetailText(self, prop):
        displayName = prop.getDisplayName()
        desc = prop.getDescription()

        if len(displayName) > 0:
            self.ui.lblPropertyName.setText(displayName)
        else:
            self.ui.lblPropertyName.setText(prop.name)

        self.ui.lblPropertyDesc.setText(desc)

    def __filterProperties(self, text):
        if len(text) == 0:
            # Empty filter, show everything
            for i in range(self.propertiesModel.rowCount()):
                self.ui.propertiesView.setRowHidden(i, QtCore.QModelIndex(), False)
            return

        # First hide all rows...
        for i in range(self.propertiesModel.rowCount()):
            self.ui.propertiesView.setRowHidden(i, QtCore.QModelIndex(), True)

        # ...then show all rows containing the filter string
        items = self.propertiesModel.findItems(text, QtCore.Qt.MatchContains)
        for item in items:
            self.ui.propertiesView.setRowHidden(item.row(), QtCore.QModelIndex(), False)

    def disable(self):
        self.entity = None
        self.clearAll()
        self.setEnabled(False)

    def enable(self):
        if self.mgr.getNumSelectedObjects() > 0:
            self.updateForSelection()

    def updateForSelection(self):
        numSelections = self.mgr.getNumSelectedObjects() if self.mgr else 0

        self.valueItemByPropName = {}

        if numSelections == 0:
            self.disable()
            return
        else:
            self.setEnabled(True)

        # Clear our filtering
        self.ui.lePropertyFilter.clear()

        # Only show one entity in the object properties..
        # and choose the most recently selected one if there are multiple selections
        selection = self.mgr.selectionMode.getObjectPropertiesTarget()
        self.entity = selection

        name = selection.getName()
        desc = selection.getDescription()

        self.ui.lblPropertyName.setText(name)
        self.ui.lblPropertyDesc.setText(desc)
        if not isinstance(selection, Entity):
            self.ui.comboClass.hide()
        else:
            self.ui.comboClass.show()
            classname = selection.getClassName()
            self.ui.comboClass.setCurrentText(classname)

        self.propertiesModel.removeRows(0, self.propertiesModel.rowCount())

        rowIdx = 0

        groupName2propList = {}
        propList = list(selection.properties.values())

        for _, prop in selection.properties.items():
            if prop.group is not None:
                if prop.group not in groupName2propList:
                    groupName2propList[prop.group] = [prop]
                else:
                    groupName2propList[prop.group].append(prop)
                propList.remove(prop)

        # Now add all the individual groups first
        for groupName, groupPropList in groupName2propList.items():
            parent = ObjectPropertiesNullItem(groupName)
            self.propertiesModel.setItem(rowIdx, 0, parent)
            rowIdx += 1

            for prop in groupPropList:
                self.createPropItemPair(prop, selection, 0, parent)

        # Add the rest of the ungrouped properties
        for prop in propList:
            self.createPropItemPair(prop, selection, rowIdx)
            rowIdx += 1

        self.ui.propertiesView.expandToDepth(1)

    def createPropItemPair(self, prop, selection, rowIdx, parent = None):
        if prop.valueType == "flags":
            valueItem = ObjectPropertiesSpawnflagsItem(self, selection, prop.name)
            self.propertiesModel.setItem(rowIdx, 0, valueItem)
            valueItem.openChildEditors()
        else:
            propItem = ObjectPropertiesItem(self, selection, prop.name, True)
            valueItem = ObjectPropertiesItem(self, selection, prop.name, False)
            valueItem.pairing = propItem
            propItem.pairing = valueItem
            if not parent:
                self.propertiesModel.setItem(rowIdx, 0, propItem)
                self.propertiesModel.setItem(rowIdx, 1, valueItem)
            else:
                parent.appendRow([propItem, valueItem])
            self.ui.propertiesView.openPersistentEditor(valueItem.index())
        self.valueItemByPropName[prop.name] = valueItem

    def updateAvailableClasses(self):
        self.ui.comboClass.clear()
        names = []
        for ent in base.fgd.entities:
            if ent.class_type in ['PointClass', 'SolidClass']:
                names.append(ent.name)
        names.sort()
        completer = QtWidgets.QCompleter(names)
        completer.setCompletionMode(QtWidgets.QCompleter.InlineCompletion)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.ui.comboClass.setCompleter(completer)
        self.ui.comboClass.addItems(names)
