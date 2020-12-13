from direct.foundry.DocObject import DocObject
from direct.foundry.ToolProperties import ToolProperties
from direct.foundry import LEUtils

from PyQt5 import QtWidgets

from direct.foundry.SelectTool import SelectTool
from direct.foundry.MoveTool import MoveTool
from direct.foundry.RotateTool import RotateTool
from direct.foundry.ScaleTool import ScaleTool
from direct.foundry.EntityTool import EntityTool
from direct.foundry.BlockTool import BlockTool
from direct.foundry.ClipTool import ClipTool
from direct.foundry.DNATool import DNATool

from functools import partial

Separator = -1

class ToolManager(DocObject):

    Tools = [
        SelectTool,
        MoveTool,
        RotateTool,
        ScaleTool,

        Separator,

        EntityTool,
        BlockTool,
        ClipTool#,

        #Separator,

        #DNATool
    ]

    def __init__(self, doc):
        DocObject.__init__(self, doc)

        self.tools = []
        self.funcs = {}
        self.currentTool = None
        self.selectTool = None
        self.connected = False

        self.toolGroup = None

        self.toolProperties = ToolProperties.getGlobalPtr()

        self.acceptGlobal('documentActivated', self.__onDocActivated)
        self.acceptGlobal('documentDeactivated', self.__onDocDeactivated)

    def cleanup(self):
        if self.currentTool:
            self.currentTool.disable()
        self.currentTool = None
        self.disconnectTools()
        self.connected = None
        for tool in self.tools:
            tool.cleanup()
        self.tools = None
        self.selectTool = None
        self.toolGroup = None
        self.funcs = None
        self.toolProperties = None

        DocObject.cleanup(self)

    def __onDocActivated(self, doc):
        if doc != self.doc:
            return

        if self.currentTool and not self.currentTool.activated:
            self.currentTool.activate()

        self.connectTools()

    def __onDocDeactivated(self, doc):
        if doc != self.doc:
            return

        if self.currentTool and self.currentTool.activated:
            self.currentTool.deactivate()

        self.disconnectTools()

    def connectTools(self):
        if self.connected:
            return

        for tool in self.tools:
            action = base.menuMgr.action(tool.KeyBind)
            action.setEnabled(True)
            action.setChecked(tool.enabled)
            action.connect(self.funcs[tool])
        self.connected = True

    def disconnectTools(self):
        if not self.connected:
            return

        for tool in self.tools:
            action = base.menuMgr.action(tool.KeyBind)
            action.setEnabled(False)
            action.setChecked(False)
            action.disconnect(self.funcs[tool])
        self.connected = False

    def switchToTool(self, tool):
        if tool == self.currentTool:
            tool.toolTriggered()
            return

        if self.currentTool:
            base.menuMgr.action(self.currentTool.KeyBind).setChecked(False)
            self.currentTool.disable()

        self.currentTool = tool
        self.currentTool.enable()
        base.menuMgr.action(self.currentTool.KeyBind).setChecked(True)

        self.doc.updateAllViews()

    def switchToSelectTool(self):
        self.switchToTool(self.selectTool)

    @staticmethod
    def addToolActions():
        toolMenu = base.menuMgr.createMenu("Tools")

        toolBar = base.toolBar
        toolGroup = QtWidgets.QActionGroup(toolBar)
        for tool in ToolManager.Tools:
            if tool == Separator:
                toolBar.addSeparator()
                toolMenu.addSeparator()
            else:
                action = base.menuMgr.addAction(tool.KeyBind, tool.Name, tool.ToolTip,
                    menu=toolMenu, toolBar=toolBar, checkable=True, enabled=False,
                    icon=LEUtils.qtResolvePath(tool.Icon))
                toolGroup.addAction(action)

    def addTool(self, tool):
        if not tool in self.tools:
            self.tools.append(tool)
            self.funcs[tool] = partial(self.switchToTool, tool)

    def addTools(self):
        for tool in self.Tools:
            if tool == Separator:
                continue
            toolInst = tool(self)
            if tool is SelectTool:
                self.selectTool = toolInst
            self.addTool(tool(self))

    def getNumTools(self):
        return len(self.tools)
