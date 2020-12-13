from PyQt5 import QtGui, QtWidgets

from direct.foundry.DocObject import DocObject

from enum import IntEnum

# What viewport type can a tool be used in?
class ToolUsage(IntEnum):
    View2D = 0
    View3D = 1
    Both = 2

class BaseTool(DocObject):

    Name = "Tool"
    KeyBind = None
    WantButton = True
    ToolTip = "Base tool"
    StatusTip = None
    Icon = None
    Usage = ToolUsage.Both

    def __init__(self, mgr):
        DocObject.__init__(self, mgr.doc)
        self.enabled = False
        self.activated = False
        self.mgr = mgr
        self.options = None

    def cleanup(self):
        self.enabled = None
        self.activated = None
        self.mgr = None
        DocObject.cleanup(self)

    def toolTriggered(self):
        pass

    def enable(self):
        print("Enable", self.Name)
        self.enabled = True
        self.activate()

    def activate(self):
        self.activated = True
        self.doc.taskMgr.add(self.__updateTask, self.Name + "-UpdateTool")
        if self.options:
            self.options.setTool(self)
            self.mgr.toolProperties.addGroup(self.options)

    def __updateTask(self, task):
        self.update()
        return task.cont

    def update(self):
        pass

    def disable(self):
        print("Disable", self.Name)
        self.deactivate()
        self.enabled = False
        self.ignoreAllGlobal()

    def deactivate(self):
        self.activated = False
        self.doc.taskMgr.remove(self.Name + "-UpdateTool")
        self.ignoreAll()
        self.mgr.toolProperties.clear()
