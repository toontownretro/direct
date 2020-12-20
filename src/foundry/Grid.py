from panda3d.core import LineSegs, NodePath, Vec4, Point3, AntialiasAttrib

from direct.foundry import LEGlobals
from direct.directbase import DirectRender

from .GridSettings import GridSettings

class Grid:

    def __init__(self, viewport):
        self.viewport = viewport
        self.doc = viewport.doc

        # So we only have to generate a grid for a step once.
        self.gridsByStep = {}

        self.gridNp = None

        self.lastStep = 0

        self.updateTask = self.doc.taskMgr.add(self.update, 'gridUpdate')

    def cleanup(self):
        self.viewport = None
        self.doc = None
        self.gridsByStep = None
        if self.gridNp:
            self.gridNp.removeNode()
        self.gridNp = None
        self.lastStep = None
        self.updateTask.remove()
        self.updateTask = None

    def removeCurrentGrid(self):
        if self.gridNp and not self.gridNp.isEmpty():
            self.gridNp.removeNode()
        self.gridNp = None

    def calcZoom(self):
        raise NotImplementedError

    def update(self, task):
        if not self.shouldRender():
            self.removeCurrentGrid()
            return task.cont

        zoom = self.calcZoom()
        step = GridSettings.DefaultStep
        low = GridSettings.Low
        high = GridSettings.High
        actualDist = step * zoom
        if GridSettings.HideSmallerToggle:
            while actualDist < GridSettings.HideSmallerThan:
                step *= GridSettings.HideFactor
                actualDist *= GridSettings.HideFactor

        if step == self.lastStep and self.gridNp:
            return task.cont

        self.removeCurrentGrid()

        self.lastStep = step

        if step in self.gridsByStep:
            self.gridNp = self.gridsByStep[step].copyTo(self.viewport.gridRoot)
            return task.cont

        segs = LineSegs()
        i = low
        while i <= high:
            color = GridSettings.GridLines
            if i == 0:
                # On zero lines, give each axis an appropriate color.
                axes = self.viewport.getGridAxes()
                color = Vec4(0, 0, 0, 1)
                color[axes[0]] = 1
                color2 = Vec4(0, 0, 0, 1)
                color2[axes[1]] = 1
            #elif (i % GridSettings.Highlight2Unit) == 0 and GridSettings.Highlight2Toggle:
            #    color = GridSettings.Highlight2
            elif (i % (step * GridSettings.Highlight1Line) == 0) and GridSettings.Highlight1Toggle:
                color = GridSettings.Highlight1
            segs.setColor(color)
            segs.moveTo(self.viewport.expand(Point3(low, 0, i)))
            segs.drawTo(self.viewport.expand(Point3(high, 0, i)))
            if i == 0:
                segs.setColor(color2)
            segs.moveTo(self.viewport.expand(Point3(i, 0, low)))
            segs.drawTo(self.viewport.expand(Point3(i, 0, high)))
            i += step

        #segs.setColor(GridSettings.BoundaryLines)
        # top
        #segs.moveTo(self.viewport.expand(Point3(low, 0, high)))
        #segs.drawTo(self.viewport.expand(Point3(high, 0, high)))
        # left
        #segs.moveTo(self.viewport.expand(Point3(low, 0, low)))
        #segs.drawTo(self.viewport.expand(Point3(low, 0, high)))
        # right
        #segs.moveTo(self.viewport.expand(Point3(high, 0, low)))
        #segs.drawTo(self.viewport.expand(Point3(high, 0, high)))
        # bottom
        #segs.moveTo(self.viewport.expand(Point3(low, 0, low)))
        #segs.drawTo(self.viewport.expand(Point3(high, 0, low)))

        np = NodePath(segs.create())
        np.setLightOff(1)
        np.setFogOff(1)
        np.hide(DirectRender.ShadowCameraBitmask | DirectRender.ReflectionCameraBitmask)
        #np.setAntialias(AntialiasAttrib.MLine)
        #loader.loadModel("models/smiley.egg.pz").reparentTo(np)
        self.gridsByStep[step] = np
        self.gridNp = np.copyTo(self.viewport.gridRoot)

        return task.cont
