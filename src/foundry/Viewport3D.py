from panda3d.core import WindowProperties, PerspectiveLens, NodePath, Fog, Vec4, Point3, LineSegs, TextNode, AntialiasAttrib
from panda3d.core import Vec3

from .Viewport import Viewport
from .FlyCam import FlyCam
from direct.foundry.Grid3D import Grid3D

from PyQt5 import QtWidgets, QtGui, QtCore

class Viewport3D(Viewport):

    def __init__(self, vpType, window, doc):
        Viewport.__init__(self, vpType, window, doc)
        self.flyCam = None

    def cleanup(self):
        self.flyCam.cleanup()
        self.flyCam = None
        Viewport.cleanup(self)

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
        self.camera.setPos(193, 247, 124)
        self.camera.setHpr(143, -18, 0)

        from panda3d.core import DirectionalLight, AmbientLight
        dlight = DirectionalLight('dlight')
        dlight.setColor((0.35, 0.35, 0.35, 1))
        dlnp = self.doc.render.attachNewNode(dlight)
        direction = -Vec3(1, 2, 3).normalized()
        dlight.setDirection(direction)
        self.doc.render.setLight(dlnp)
        self.dlnp = dlnp
        alight = AmbientLight('alight')
        alight.setColor((0.65, 0.65, 0.65, 1))
        alnp = self.doc.render.attachNewNode(alight)
        self.doc.render.setLight(alnp)

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
