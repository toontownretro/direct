# Purpose: Manages the QActions that are bound to hotkeys

from .KeyBind import KeyBind
from .KeyBinds import KeyBindsByID

from direct.foundry import LEGlobals, LEUtils

from PyQt5 import QtWidgets, QtGui, QtCore

class EditorAction(QtWidgets.QAction):

    def __init__(self, text, parent, checkable, keyBindID):
        QtWidgets.QAction.__init__(self, text, parent)
        self.keyBindID = keyBindID
        keyBind = KeyBindsByID[keyBindID]
        self.keyBind = keyBind

    def connect(self, func):
        self.triggered.connect(func)

    def disconnect(self, func):
        self.triggered.disconnect(func)

    def enable(self):
        self.setEnabled(True)

    def disable(self):
        self.setEnabled(False)

class MenuManager:

    def __init__(self):
        # Key bind ID -> QAction
        self.actions = {}

    def action(self, id):
        return self.actions[id]

    def connect(self, keyBindID, func):
        self.action(keyBindID).connect(func)

    def disconnect(self, keyBindID, func):
        self.action(keyBindID).disconnect(func)

    def enableAction(self, keyBindID):
        action = self.actions.get(keyBindID, None)
        if action:
            action.setEnabled(True)

    def disableAction(self, keyBindID):
        action = self.actions.get(keyBindID, None)
        if action:
            action.setEnabled(False)

    def addAction(self, keyBindID, text, desc, icon = None, toolBar = False, checkable = False, menu = None, enabled = True):
        action = EditorAction(text, base.qtWindow, checkable, keyBindID)
        if icon is not None:
            icon = QtGui.QIcon(LEUtils.qtResolvePath(icon))
            action.setIcon(icon)
        action.setCheckable(checkable)
        action.setToolTip(desc)
        action.setStatusTip(desc)
        action.setIconVisibleInMenu(False)
        action.setShortcutVisibleInContextMenu(True)
        action.setEnabled(enabled)
        if toolBar:
            if isinstance(toolBar, bool):
                base.topBar.addAction(action)
            else:
                toolBar.addAction(action)
        if menu:
            menu.addAction(action)
        action.setShortcut(action.keyBind.shortcut)
        self.actions[keyBindID] = action
        return action

    def createToolBar(self, name):
        toolBar = base.qtWindow.addToolBar(name)
        toolBar.setIconSize(QtCore.QSize(24, 24))
        toolBar.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        label = QtWidgets.QLabel(name)
        label.setAlignment(QtCore.Qt.AlignCenter)
        toolBar.addWidget(label)
        return toolBar

    def createMenu(self, name):
        menu = QtWidgets.QMenu(name, base.menuBar)
        base.menuBar.addMenu(menu)
        return menu

    def addMenuItems(self):
        editToolBar = self.createToolBar("Editing:")

        fileMenu = self.createMenu("File")
        self.addAction(KeyBind.FileNew, "New", "Create a new map", menu=fileMenu)
        self.addAction(KeyBind.FileOpen, "Open...", "Open an existing map", menu=fileMenu)
        self.addAction(KeyBind.FileClose, "Close", "Close the map", toolBar=editToolBar, menu=fileMenu, enabled=False,
            icon="icons/editor-close.png")
        self.addAction(KeyBind.FileCloseAll, "Close All", "Close all open maps", menu=fileMenu, enabled=False)
        fileMenu.addSeparator()
        self.addAction(KeyBind.FileSave, "Save", "Save the map", toolBar=editToolBar, menu=fileMenu, enabled=False,
            icon="icons/editor-save.png")
        self.addAction(KeyBind.FileSaveAs, "Save As...", "Save the map as", menu=fileMenu, enabled=False)
        self.addAction(KeyBind.FileSaveAll, "Save All", "Save all maps", menu=fileMenu, enabled=False)
        fileMenu.addSeparator()
        self.addAction(KeyBind.Run, "Run...", "Run the map", menu=fileMenu, enabled=False)
        fileMenu.addSeparator()
        self.addAction(KeyBind.Exit, "Exit", "Exit %s" % LEGlobals.AppName, menu=fileMenu)

        editMenu = self.createMenu("Edit")
        self.addAction(KeyBind.Undo, "Undo", "Undo the previous action", menu=editMenu, toolBar=editToolBar, enabled=False,
            icon="icons/editor-undo.png")
        self.addAction(KeyBind.Redo, "Redo", "Redo the previous action", menu=editMenu, toolBar=editToolBar, enabled=False,
            icon="icons/editor-redo.png")
        editMenu.addSeparator()
        self.addAction(KeyBind.Delete, "Delete", "Delete the selected objects", menu=editMenu, enabled=False)
        self.addAction(KeyBind.Cut, "Cut", "Cut the selected objects", menu=editMenu, enabled=False)
        self.addAction(KeyBind.Copy, "Copy", "Copy the selected objects", menu=editMenu, enabled=False)
        self.addAction(KeyBind.Paste, "Paste", "Paste objects", menu=editMenu, enabled=False)
        editMenu.addSeparator()
        self.addAction(KeyBind.GroupSelected, "Group", "Group the selected objects", menu=editMenu, enabled=False)
        self.addAction(KeyBind.UngroupSelected, "Ungroup", "Ungroup the selected objects", menu=editMenu, enabled=False)
        editMenu.addSeparator()
        self.addAction(KeyBind.TieToWorld, "Tie to World", "Tie selected objects to world", menu=editMenu, enabled=False)
        self.addAction(KeyBind.TieToEntity, "Tie to Entity", "Tie selected objects to entity", menu=editMenu, enabled=False)
        editMenu.addSeparator()
        self.addAction(KeyBind.ToggleGridSnap, "Grid Snap", "Toggle snap to grid", menu=editMenu, enabled=False, toolBar=editToolBar, checkable=True,
                        icon="icons/editor-grid-snap.png")
        self.addAction(KeyBind.IncGridSize, "Increase Grid Size", "Increase grid size", menu=editMenu, enabled=False, toolBar=editToolBar,
                        icon="icons/editor-inc-grid.png")
        self.addAction(KeyBind.DecGridSize, "Decrease Grid Size", "Decrease grid size", menu=editMenu, enabled=False, toolBar=editToolBar,
                        icon="icons/editor-dec-grid.png")

        viewMenu = self.createMenu("View")
        self.addAction(KeyBind.ViewQuads, "Quad View", "Arrange viewports in quad splitter", menu=viewMenu, enabled=False)
        self.addAction(KeyBind.View3D, "3D Perspective", "Focus 3D Perspective", menu=viewMenu, enabled=False)
        self.addAction(KeyBind.ViewXY, "2D Top", "Focus 2D Top", menu=viewMenu, enabled=False)
        self.addAction(KeyBind.ViewYZ, "2D Side", "Focus 2D Side", menu=viewMenu, enabled=False)
        self.addAction(KeyBind.ViewXZ, "2D Front", "Focus 2D Front", menu=viewMenu, enabled=False)
        viewMenu.addSeparator()
        self.addAction(KeyBind.Toggle2DGrid, "2D Grid", "Toggle 2D grid", menu=viewMenu, toolBar=editToolBar, enabled=False, checkable=True,
            icon="icons/editor-grid-2d.png")
        self.addAction(KeyBind.Toggle3DGrid, "3D Grid", "Toggle 3D grid", menu=viewMenu, toolBar=editToolBar, enabled=False, checkable=True,
            icon="icons/editor-grid-3d.png")
        viewMenu.addSeparator()
        self.addAction(KeyBind.ListScene, "List Scene Graph", "Lists the scene graph of the entire level editor.  For debugging purposes.",
                       menu=viewMenu, enabled=False)

        self.editMenu = editMenu
