from panda3d.core import RenderState, ColorAttrib, Vec4, Point3, GeomNode

from direct.foundry.ObjectPropertiesWindow import ObjectPropertiesWindow
from direct.foundry.Box import Box
from direct.foundry.GeomView import GeomView
from direct.foundry.ViewportType import VIEWPORT_2D_MASK, VIEWPORT_3D_MASK
from direct.foundry import RenderModes
from direct.foundry import LEGlobals
from .SelectionType import SelectionType
from direct.foundry.Delete import Delete
from direct.foundry.ChangeSelectionMode import ChangeSelectionMode
from direct.foundry.DocObject import DocObject

from .GroupsMode import GroupsMode
from .ObjectMode import ObjectMode
from .FaceMode import FaceMode
from .VertexMode import VertexMode

from enum import IntEnum
from functools import partial

from PyQt5 import QtWidgets, QtCore

Bounds3DState = RenderState.make(
    ColorAttrib.makeFlat(Vec4(1, 1, 0, 1))
)

Bounds2DState = RenderModes.DashedLineNoZ()
Bounds2DState = Bounds2DState.setAttrib(ColorAttrib.makeFlat(Vec4(1, 1, 0, 1)))

class SelectionManager(DocObject):

    Modes = [
        GroupsMode,
        ObjectMode,
        FaceMode,
        VertexMode
    ]

    def __init__(self, doc):
        DocObject.__init__(self, doc)
        self.selectedObjects = []
        self.selectionMins = Point3()
        self.selectionMaxs = Point3()
        self.selectionCenter = Point3()

        # We'll select groups by default
        self.selectionModes = {}
        self.funcs = {}
        self.selectionMode = None
        self.connected = False

        self.acceptGlobal('documentActivated', self.__onDocActivated)
        self.acceptGlobal('documentDeactivated', self.__onDocDeactivated)
        self.accept('objectTransformChanged', self.handleObjectTransformChange)
        self.accept('mapObjectBoundsChanged', self.handleMapObjectBoundsChanged)

        self.addSelectionModes()

        self.setSelectionMode(SelectionType.Groups)

    def cleanup(self):
        self.selectedObjects = None
        self.selectionMins = None
        self.selectionMaxs = None
        self.selectionCenter = None
        self.disconnectModes()
        self.connected = None
        self.funcs = None
        if self.selectionMode:
            self.selectionMode.disable()
        self.selectionMode = None
        for mode in self.selectionModes.values():
            mode.cleanup()
        self.selectionModes = None
        self.selectionMode = None
        self.connected = None
        DocObject.cleanup(self)

    def __onDocActivated(self, doc):
        if doc != self.doc:
            return

        if self.selectionMode and not self.selectionMode.activated:
            self.selectionMode.activate()

        self.connectModes()

    def connectModes(self):
        if self.connected:
            return

        for mode in self.selectionModes.values():
            action = base.menuMgr.action(mode.KeyBind)
            action.setChecked(mode.enabled)
            action.setEnabled(True)
            action.connect(self.funcs[mode])

        self.connected = True

    def __onDocDeactivated(self, doc):
        if doc != self.doc:
            return

        if self.selectionMode and self.selectionMode.activated:
            self.selectionMode.deactivate()

        self.disconnectModes()

    def disconnectModes(self):
        if not self.connected:
            return

        for mode in self.selectionModes.values():
            action = base.menuMgr.action(mode.KeyBind)
            action.setChecked(False)
            action.setEnabled(False)
            action.disconnect(self.funcs[mode])

        self.connected = False

    @staticmethod
    def addModeActions():
        editMenu = base.menuMgr.editMenu
        editMenu.addSeparator()

        selectBar = base.menuMgr.createToolBar("Select:")
        selectBar.setIconSize(QtCore.QSize(24, 24))
        selectBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        selectMenu = editMenu.addMenu("Select")
        group = QtWidgets.QActionGroup(selectBar)
        for mode in SelectionManager.Modes:
            action = base.menuMgr.addAction(mode.KeyBind, mode.Name, mode.Desc, toolBar=selectBar,
                menu=selectMenu, checkable=True, enabled=False, icon=mode.Icon)
            group.addAction(action)

    def changeSelectionMode(self, mode):
        modeInst = self.selectionModes[mode]
        base.actionMgr.performAction("Select %s" % modeInst.Name, ChangeSelectionMode(mode))

    def getSelectionKey(self):
        return self.selectionMode.Key

    def getSelectionMask(self):
        return self.selectionMode.Mask

    def isTransformAllowed(self, bits):
        return (self.selectionMode.TransformBits & bits) != 0

    def addSelectionMode(self, modeInst):
        self.selectionModes[modeInst.Type] = modeInst
        self.funcs[modeInst] = partial(self.changeSelectionMode,  modeInst.Type)

    def addSelectionModes(self):
        for mode in self.Modes:
            self.addSelectionMode(mode(self))

    def setSelectionMode(self, mode):
        if self.selectionMode is not None:
            oldMode = self.selectionMode.Type
            oldModeInst = self.selectionMode
        else:
            oldMode = None
            oldModeInst = None
        if mode != self.selectionMode and self.selectionMode is not None:
            self.selectionMode.disable()
        elif mode == self.selectionMode:
            return
        self.deselectAll()
        self.selectionMode = self.selectionModes[mode]
        self.selectionMode.enable()
        self.send('selectionModeChanged', [oldModeInst, self.selectionMode])

    def handleMapObjectBoundsChanged(self, mapObject):
        if mapObject in self.selectedObjects:
            self.updateSelectionBounds()
            self.send('selectedObjectBoundsChanged', [mapObject])

    def handleObjectTransformChange(self, entity):
        if entity in self.selectedObjects:
            self.updateSelectionBounds()
            self.send('selectedObjectTransformChanged', [entity])

    def deleteSelectedObjects(self):
        if len(self.selectedObjects) == 0:
            # Nothing to delete.
            return

        selected = list(self.selectedObjects)
        base.actionMgr.performAction("Delete %i object(s)" % len(selected), Delete(selected))
        self.selectedObjects = []
        self.updateSelectionBounds()
        self.send('selectionsChanged')

    def hasSelectedObjects(self):
        return len(self.selectedObjects) > 0

    def getNumSelectedObjects(self):
        return len(self.selectedObjects)

    def isSelected(self, obj):
        return obj in self.selectedObjects

    def deselectAll(self, update = True):
        for obj in self.selectedObjects:
            obj.deselect()
        self.selectedObjects = []
        if update:
            self.updateSelectionBounds()
            self.send('selectionsChanged')

    def singleSelect(self, obj):
        self.deselectAll(False)
        self.select(obj)

    def multiSelect(self, listOfObjs):
        self.deselectAll(False)
        for obj in listOfObjs:
            self.select(obj, False)
        self.updateSelectionBounds()
        self.send('selectionsChanged')

    def deselect(self, obj, updateBounds = True):
        if obj in self.selectedObjects:
            self.selectedObjects.remove(obj)
            obj.deselect()

            if updateBounds:
                self.updateSelectionBounds()
                self.send('selectionsChanged')

    def select(self, obj, updateBounds = True):
        if not obj in self.selectedObjects:
            self.selectedObjects.append(obj)
            obj.select()

            if updateBounds:
                self.updateSelectionBounds()
                self.send('selectionsChanged')

    def updateSelectionBounds(self):

        if len(self.selectedObjects) == 0:
            base.qtWindow.selectedLabel.setText("No selection.")
            self.selectionMins = Point3()
            self.selectionMaxs = Point3()
            self.selectionCenter = Point3()
            return
        else:
            if len(self.selectedObjects) == 1:
                obj = self.selectedObjects[0]
                base.qtWindow.selectedLabel.setText(obj.getName())
            else:
                base.qtWindow.selectedLabel.setText("Selected %i objects." % len(self.selectedObjects))

        mins = Point3(9999999)
        maxs = Point3(-9999999)

        for obj in self.selectedObjects:
            objMins, objMaxs = obj.getBounds(base.render)
            if objMins.x < mins.x:
                mins.x = objMins.x
            if objMins.y < mins.y:
                mins.y = objMins.y
            if objMins.z < mins.z:
                mins.z = objMins.z
            if objMaxs.x > maxs.x:
                maxs.x = objMaxs.x
            if objMaxs.y > maxs.y:
                maxs.y = objMaxs.y
            if objMaxs.z > maxs.z:
                maxs.z = objMaxs.z

        self.selectionMins = mins
        self.selectionMaxs = maxs
        self.selectionCenter = (mins + maxs) / 2.0
