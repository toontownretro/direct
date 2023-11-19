from panda3d.core import Vec3, Point2, WindowProperties, NodePath, SamplerState

from direct.gui.DirectGui import OnscreenImage
from direct.foundry import KeyBinds
from direct.foundry.KeyBind import KeyBind
from direct.foundry.DocObject import DocObject
from direct.foundry import LEConfig

import math

from PyQt5 import QtWidgets, QtGui, QtCore

class FlyCam(DocObject):

    def __init__(self, viewport):
        DocObject.__init__(self, viewport.doc)

        self.viewport = viewport

        self.enabled = False
        self.mouseSensitivity = 0.3
        self.cameraSpeed = (500 / 16.0) * LEConfig.unit_scale.value
        self.timeToSpeed = 0.5 # seconds
        self.moveStart = 0.0
        self.cameraRotateSpeed = 75.0
        self.cameraSmooth = 0.7
        self.slideFactor = 0.75
        self.maxPitch = 90
        self.minPitch = -90
        self.diagonalFactor = math.sqrt(2.0) / 2.0
        self.lastSpeeds = Vec3(0)
        self.moving = False

        self.cursor = QtGui.QCursor()
        self.cursor.setShape(QtCore.Qt.BlankCursor)

        tex = base.loader.loadTexture('icons/editor-crosshair.png')
        tex.setMinfilter(SamplerState.FTLinear)
        tex.setMagfilter(SamplerState.FTLinear)
        crosshair = OnscreenImage(tex)
        crosshair.setTransparency(True)
        crosshair.setScale(0.04)
        crosshair.reparentTo(NodePath())
        self.crosshair = crosshair

        self.inputState = {}

        self.addInput("forward", KeyBind.Forward3DView)
        self.addInput("reverse", KeyBind.Back3DView)
        self.addInput("slideLeft", KeyBind.Left3DView)
        self.addInput("slideRight", KeyBind.Right3DView)
        self.addInput("floatDown", KeyBind.Down3DView)
        self.addInput("floatUp", KeyBind.Up3DView)
        self.addInput("lookUp", KeyBind.LookUp3DView)
        self.addInput("lookDown", KeyBind.LookDown3DView)
        self.addInput("lookRight", KeyBind.LookRight3DView)
        self.addInput("lookLeft", KeyBind.LookLeft3DView)

        self.accept(KeyBinds.getPandaShortcut(KeyBind.FlyCam), self.handleZ)

        self.doc.taskMgr.add(self.__flyCamTask, 'flyCam')

    def cleanup(self):
        self.viewport = None
        self.doc.taskMgr.remove('flyCam')
        self.inputState = None
        self.crosshair.destroy()
        self.crosshair = None
        self.cursor = None
        self.moving = None
        self.lastSpeeds = None
        self.diagonalFactor = None
        self.maxPitch = None
        self.minPitch = None
        self.slideFactor = None
        self.cameraSmooth = None
        self.cameraRotateSpeed = None
        self.cameraSpeed = None
        self.moveStart = None
        self.enabled = None
        self.mouseSensitivity = None
        DocObject.cleanup(self)

    def addInput(self, name, keyBindID):
        self.inputState[name] = False
        shortcut = KeyBinds.getPandaShortcut(keyBindID)
        self.accept(shortcut, self.__keyDown, [name])
        self.accept(shortcut + '-up', self.__keyUp, [name])

    def __keyDown(self, name):
        self.inputState[name] = True

    def __keyUp(self, name):
        self.inputState[name] = False

    def isSet(self, name):
        return self.inputState[name]

    def handleZ(self):
        if self.viewport.mouseWatcher.hasMouse():
            self.setEnabled(not self.enabled)
            self.viewport.updateView()

    def setEnabled(self, flag):
        if flag:
            if not self.enabled:
                self.viewport.setCursor(self.cursor)
                self.viewport.centerCursor(self.cursor)
                self.crosshair.reparentTo(self.viewport.aspect2d)
        else:
            if self.enabled:
                self.crosshair.reparentTo(NodePath())
                self.viewport.unsetCursor()

        self.enabled = flag

    def __flyCamTask(self, task):

        camera = self.viewport.camera
        win = self.viewport.win

        dt = globalClock.getDt()
        goalSpeeds = Vec3(0)

        md = win.getPointer(0)
        if md.getInWindow():
            if self.enabled:
                center = Point2(win.getXSize() // 2, win.getYSize() // 2)
                dx = center.getX() - md.getX()
                dy = center.getY() - md.getY()
                camera.setH(camera.getH() + (dx * self.mouseSensitivity))
                camera.setP(camera.getP() + (dy * self.mouseSensitivity))
                self.viewport.centerCursor(self.cursor)
                if (dx != 0 or dy != 0):
                    self.viewport.updateView()

            # linear movement WASD+QE
            goalDir = Vec3(0)
            if self.isSet("forward"):
                goalDir[1] += 1
            if self.isSet("reverse"):
                goalDir[1] -= 1
            if self.isSet("slideLeft"):
                goalDir[0] -= 1
            if self.isSet("slideRight"):
                goalDir[0] += 1
            if self.isSet("floatUp"):
                goalDir[2] += 1
            if self.isSet("floatDown"):
                goalDir[2] -= 1

            if abs(goalDir[0]) and not abs(goalDir[1]):
                goalDir[0] *= self.slideFactor
            elif abs(goalDir[0]) and abs(goalDir[1]):
                goalDir[0] *= self.diagonalFactor
                goalDir[1] *= self.diagonalFactor

            # rotational movement arrow keys
            goalRot = Vec3(0)
            if self.isSet("lookLeft"):
                goalRot[0] += 1
            if self.isSet("lookRight"):
                goalRot[0] -= 1
            if self.isSet("lookUp"):
                goalRot[1] += 1
            if self.isSet("lookDown"):
                goalRot[1] -= 1
            camera.setH(camera.getH() + (goalRot[0] * self.cameraRotateSpeed * dt))
            camera.setP(camera.getP() + (goalRot[1] * self.cameraRotateSpeed * dt))

            # Limit the camera pitch so it doesn't go crazy
            if camera.getP() > self.maxPitch:
                camera.setP(self.maxPitch)
            elif camera.getP() < self.minPitch:
                camera.setP(self.minPitch)

            goalSpeeds = goalDir * self.cameraSpeed

        speeds = Vec3(goalSpeeds)
        if speeds.lengthSquared() > 0.001:
            now = globalClock.getFrameTime()
            if not self.moving:
                self.moving = True
                self.moveStart = now
            speedFactor = min((now - self.moveStart) / self.timeToSpeed, 1.0)
            speeds *= dt * speedFactor
            # dont have float value be affected by direction, always completely up or down
            camera.setPos(camera.getPos() + camera.getQuat().xform(Vec3(speeds[0], speeds[1], 0)))
            camera.setZ(camera, speeds[2])

            self.viewport.updateView()
        else:
            self.moving = False

        # should never have a roll in the camera
        camera.setR(0)

        self.lastSpeeds = speeds

        return task.cont
