from panda3d.core import WindowProperties, PerspectiveLens, NodePath, Fog, Vec4, Point3, LineSegs, TextNode, AntialiasAttrib
from panda3d.core import Vec3, BitMask32

from .Viewport import Viewport
from .ViewportType import VIEWPORT_3D
from .FlyCam import FlyCam
from direct.directbase import DirectRender
from direct.foundry.Grid3D import Grid3D

from PyQt5 import QtWidgets, QtGui, QtCore

class Viewport3D(Viewport):

    def __init__(self, vpType, window, doc):
        Viewport.__init__(self, vpType, window, doc)
        self.flyCam = None
        self.pp = None
        self.ppTask = None

    def cleanup(self):
        self.flyCam.cleanup()
        self.flyCam = None
        self.ppTask.remove()
        self.ppTask = None
        self.pp.cleanup()
        self.pp = None
        Viewport.cleanup(self)

    def getViewportFullMask(self):
        return self.getViewportMask() | DirectRender.ShadowCameraBitmask | DirectRender.ReflectionCameraBitmask

    def mouseMove(self):
        base.qtWindow.coordsLabel.setText("")

    def tick(self):
        Viewport.tick(self)
        if self.gizmo:
            quat = render.getQuat(self.cam)
            self.gizmo.xNp.lookAt(quat.getRight())
            self.gizmo.yNp.lookAt(quat.getForward())
            self.gizmo.zNp.lookAt(quat.getUp())

    def initialize(self):
        Viewport.initialize(self)
        self.flyCam = FlyCam(self)

        self.lens.setFov(90)
        self.lens.setNearFar(0.1, 5000)

        # Set a default camera position + angle
        self.camera.setPos(193 / 16, 247 / 16, 124 / 16)
        self.camera.setHpr(143, -18, 0)

        # FIXME: Move this to direct
        #from toontown.toonbase.ToontownPostProcess import ToontownPostProcess
        #pp = ToontownPostProcess()
        #pp.startup(self.win)
        #pp.addCamera(self.cam, 0)
        #pp.setup()
        #self.pp = pp
        #self.ppTask = self.doc.taskMgr.add(self.__updatePostProcess, "doc.updatePostProcess")

    def onResize(self, newsize):
        if self.pp:
            self.pp.windowEvent()

    def __updatePostProcess(self, task):
        self.pp.update()
        return task.cont

    def makeLens(self):
        return PerspectiveLens()

    def makeGrid(self):
        self.grid = Grid3D(self)
        #self.gridRoot.setP(-90)

        # Use a fog effect to fade out the 3D grid with distance.
        # This hides the ugly banding and aliasing you see on the grid
        # from a distance, and looks quite nice.
        #gridFog = Fog('gridFog')
        #gridFog.setColor(self.ClearColor)
        #gridFog.setExpDensity(0.0015)
        #self.gridRoot.setFog(gridFog)

    def getGridAxes(self):
        # Show X and Y on the grid
        return (0, 1)

    def getGizmoAxes(self):
        return (0, 1, 2)

    def expand(self, point):
        return Point3(point[0], point[2], 0)

    def draw(self):
        messenger.send('draw3D', [self])
