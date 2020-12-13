from panda3d.core import Point2, WindowProperties

from direct.foundry.DocObject import DocObject

class ViewportManager(DocObject):

    def __init__(self, doc):
        DocObject.__init__(self, doc)
        self.viewports = []
        self.activeViewport = None
        self.lastMouse = None

        self.acceptGlobal('documentActivated', self.__onDocActivated)
        self.acceptGlobal('documentDeactivated', self.__onDocDeactivated)

        self.tickTask = self.doc.taskMgr.add(self.__update, 'updateViewports', sort = -100)
        self.accept('mouse1', self.m1Down)
        self.accept('mouse1-up', self.m1Up)
        self.accept('mouse2', self.m2Down)
        self.accept('mouse2-up', self.m2Up)
        self.accept('mouse3', self.m3Down)
        self.accept('mouse3-up', self.m3Up)
        self.accept('wheel_down', self.wheelDown)
        self.accept('wheel_up', self.wheelUp)
        self.accept('f9', self.screenshot)

    def cleanup(self):
        self.ignoreAll()
        self.ignoreAllGlobal()
        for vp in self.viewports:
            vp.cleanup()
        self.viewports = None
        self.activeViewport = None
        self.lastMouse = None
        self.tickTask.remove()
        self.tickTask = None
        DocObject.cleanup(self)

    def __onDocActivated(self, doc):
        if doc != self.doc:
            return

        for vp in self.viewports:
            vp.enable()

    def __onDocDeactivated(self, doc):
        if doc != self.doc:
            return

        for vp in self.viewports:
            vp.disable()

    def screenshot(self):
        pass
        #if self.activeViewport:
            #ScreenshotHandler.takeScreenshot(self.activeViewport.win, False)

    def m1Down(self):
        if self.activeViewport:
            self.activeViewport.mouse1Down()

    def m1Up(self):
        if self.activeViewport:
            self.activeViewport.mouse1Up()

    def m2Down(self):
        if self.activeViewport:
            self.activeViewport.mouse2Down()

    def m2Up(self):
        if self.activeViewport:
            self.activeViewport.mouse2Up()

    def m3Down(self):
        if self.activeViewport:
            self.activeViewport.mouse3Down()

    def m3Up(self):
        if self.activeViewport:
            self.activeViewport.mouse3Up()

    def wheelDown(self):
        if self.activeViewport:
            self.activeViewport.wheelDown()

    def wheelUp(self):
        if self.activeViewport:
            self.activeViewport.wheelUp()

    def __update(self, task):
        active = None
        for vp in self.viewports:
            if vp.mouseWatcher.hasMouse():
                active = vp
            vp.tick()

        if active and (not self.activeViewport or self.activeViewport != active):
            active.mouseEnter()
            self.doc.messenger.send('mouseEnter', [active])
        elif not active and self.activeViewport:
            self.activeViewport.mouseExit()
            self.doc.messenger.send('mouseExit', [self.activeViewport])

        if active and active == self.activeViewport:
            mouse = active.mouseWatcher.getMouse()
            if not self.lastMouse or self.lastMouse != mouse:
                active.mouseMove()
                self.doc.messenger.send('mouseMoved', [active])
            self.lastMouse = Point2(mouse)

        self.activeViewport = active

        return task.cont

    def hasActiveViewport(self):
        return self.activeViewport is not None

    def addViewport(self, vp):
        if not vp in self.viewports:
            self.viewports.append(vp)

    def removeViewport(self, vp):
        if vp in self.viewports:
            self.viewports.remove(vp)

    def getNumViewports(self):
        return len(self.viewports)
