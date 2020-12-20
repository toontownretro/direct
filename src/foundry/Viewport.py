# Filename: Viewport.py
# Created by:  Brian Lach (June 4, 2020)

from panda3d.core import Camera, BitMask32, WindowProperties, GraphicsPipe, FrameBufferProperties
from panda3d.core import MouseAndKeyboard, ButtonThrower, MouseWatcher, KeyboardButton, NodePath
from panda3d.core import CollisionRay, CollisionNode, CollisionHandlerQueue, Mat4
from panda3d.core import Vec4, ModifierButtons, Point2, Vec3, Point3, Vec2, ModelNode, LVector2i, LPoint2i
from panda3d.core import OmniBoundingVolume, OrthographicLens, MouseButton

from direct.foundry import LEGlobals
from direct.directbase import DirectRender

from .ViewportType import *
from .ViewportGizmo import ViewportGizmo
from direct.foundry.Ray import Ray
from direct.foundry import LEUtils

from direct.showbase.DirectObject import DirectObject

from PyQt5 import QtWidgets, QtGui, QtCore

# Base viewport class
class Viewport(QtWidgets.QWidget, DirectObject):

    ClearColor = LEGlobals.vec3GammaToLinear(Vec4(0.361, 0.361, 0.361, 1.0))

    def __init__(self, vpType, window, doc):
        DirectObject.__init__(self)
        QtWidgets.QWidget.__init__(self, window)
        self.doc = doc
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setMouseTracking(True)

        self.qtWindow = None
        self.qtWidget = None

        self.window = window
        self.type = vpType

        self.spec = VIEWPORT_SPECS[self.type]

        self.lens = None
        self.camNode = None
        self.camera = None
        self.cam = None
        self.win = None
        self.displayRegion = None
        self.mouseWatcher = None
        self.mouseWatcherNp = None
        self.buttonThrower = None
        self.clickRay = None
        self.clickNode = None
        self.clickNp = None
        self.clickQueue = None
        self.tickTask = None
        self.zoom = 1.0
        self.gizmo = None
        self.inputDevice = None
        self.mouseAndKeyboard = None
        self.lastRenderTime = 0.0
        self.enabled = False
        self.needsUpdate = True

        # 2D stuff copied from ShowBase :(
        self.camera2d = None
        self.cam2d = None
        self.render2d = None
        self.aspect2d = None
        self.a2dBackground = None
        self.a2dTop = None
        self.a2dBottom = None
        self.a2dLeft = None
        self.a2dRight = None
        self.a2dTopCenter = None
        self.a2dTopCenterNs = None
        self.a2dBottomCenter = None
        self.a2dBottomCenterNs = None
        self.a2dRightCenter = None
        self.a2dRightCenterNs = None
        self.a2dTopLeft = None
        self.a2dTopLeftNs = None
        self.a2dTopRight = None
        self.a2dTopRightNs = None
        self.a2dBottomLeft = None
        self.a2dBottomLeftNs = None
        self.a2dBottomRight = None
        self.a2dBottomRightNs = None
        self.__oldAspectRatio = None

        self.gridRoot = self.doc.render.attachNewNode("gridRoot")
        self.gridRoot.setLightOff(1)
        #self.gridRoot.setBSPMaterial("phase_14/materials/unlit.mat")
        #self.gridRoot.setDepthWrite(False)
        self.gridRoot.setBin("background", 0)
        self.gridRoot.hide(~self.getViewportMask())

        self.grid = None

    def updateView(self, now = False):
        if now:
            self.renderView()
        else:
            self.needsUpdate = True

    def getGizmoAxes(self):
        raise NotImplementedError

    def getMouseRay(self, collRay = False):
        ray = CollisionRay()
        ray.setFromLens(self.camNode, self.getMouse())
        if collRay:
            return ray
        else:
            return Ray(ray.getOrigin(), ray.getDirection())

    def hasMouse(self):
        return self.mouseWatcher.hasMouse()

    def getMouse(self):
        if self.mouseWatcher.hasMouse():
            return self.mouseWatcher.getMouse()
        return Point2(0, 0)

    def is3D(self):
        return self.type == VIEWPORT_3D

    def is2D(self):
        return self.type != VIEWPORT_3D

    def makeGrid(self):
        raise NotImplementedError

    def getViewportMask(self):
        return BitMask32.bit(self.type)

    def getViewportFullMask(self):
        return self.getViewportMask()

    def makeLens(self):
        raise NotImplementedError

    def getGridAxes(self):
        raise NotImplementedError

    def expand(self, point):
        return point

    def initialize(self):
        self.lens = self.makeLens()
        self.camera = self.doc.render.attachNewNode(ModelNode("viewportCameraParent"))
        self.camNode = Camera("viewportCamera")
        self.camNode.setLens(self.lens)
        self.camNode.setCameraMask(self.getViewportMask())
        self.cam = self.camera.attachNewNode(self.camNode)

        winprops = WindowProperties.getDefault()
        winprops.setParentWindow(int(self.winId()))
        winprops.setForeground(False)
        winprops.setUndecorated(True)

        gsg = self.doc.gsg

        output = base.graphicsEngine.makeOutput(
            base.pipe, "viewportOutput", 0,
            FrameBufferProperties.getDefault(),
            winprops, (GraphicsPipe.BFFbPropsOptional | GraphicsPipe.BFRequireWindow),
            gsg
        )

        self.qtWindow = QtGui.QWindow.fromWinId(output.getWindowHandle().getIntHandle())
        self.qtWidget = QtWidgets.QWidget.createWindowContainer(self.qtWindow, self,
            QtCore.Qt.WindowDoesNotAcceptFocus | QtCore.Qt.WindowTransparentForInput | QtCore.Qt.WindowStaysOnBottomHint | QtCore.Qt.BypassWindowManagerHint | QtCore.Qt.SubWindow)#,
            #(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowDoesNotAcceptFocus
            #| QtCore.Qt.WindowTransparentForInput | QtCore.Qt.BypassWindowManagerHint
            #| QtCore.Qt.SubWindow | QtCore.Qt.WindowStaysOnBottomHint))
        self.qtWidget.setFocusPolicy(QtCore.Qt.NoFocus)

        self.inputDevice = output.getInputDevice(0)

        assert output is not None, "Unable to create viewport output!"

        dr = output.makeDisplayRegion()
        dr.disableClears()
        dr.setCamera(self.cam)
        self.displayRegion = dr

        output.disableClears()
        output.setClearColor(Viewport.ClearColor)
        output.setClearColorActive(True)
        output.setClearDepthActive(True)
        output.setActive(True)

        self.win = output

        # keep track of the mouse in this viewport
        mak = MouseAndKeyboard(self.win, 0, "mouse")
        mouse = base.dataRoot.attachNewNode(mak)
        self.mouseAndKeyboard = mouse
        self.mouseWatcher = MouseWatcher()
        self.mouseWatcher.setDisplayRegion(self.displayRegion)
        mw = mouse.attachNewNode(self.mouseWatcher)
        self.mouseWatcherNp = mw

        # listen for keyboard and mouse events in this viewport
        bt = ButtonThrower("kbEvents")
        bt.setButtonDownEvent("btndown")
        bt.setButtonUpEvent("btnup")
        mods = ModifierButtons()
        mods.addButton(KeyboardButton.shift())
        mods.addButton(KeyboardButton.control())
        mods.addButton(KeyboardButton.alt())
        mods.addButton(KeyboardButton.meta())
        bt.setModifierButtons(mods)
        self.buttonThrower = mouse.attachNewNode(bt)

        # collision objects for clicking on objects from this viewport
        self.clickRay = CollisionRay()
        self.clickNode = CollisionNode("viewportClickRay")
        self.clickNode.addSolid(self.clickRay)
        self.clickNp = NodePath(self.clickNode)
        self.clickQueue = CollisionHandlerQueue()

        self.setupRender2d()
        self.setupCamera2d()

        self.gizmo = ViewportGizmo(self)

        self.doc.viewportMgr.addViewport(self)

        self.makeGrid()

    def cleanup(self):
        self.grid.cleanup()
        self.grid = None
        self.gridRoot.removeNode()
        self.gridRoot = None

        self.lens = None
        self.camNode = None
        self.cam.removeNode()
        self.cam = None
        self.camera.removeNode()
        self.camera = None
        self.spec = None
        self.doc = None
        self.type = None
        self.window = None
        self.zoom = None
        self.gizmo.cleanup()
        self.gizmo = None
        self.clickNp.removeNode()
        self.clickNp = None
        self.clickQueue.clearEntries()
        self.clickQueue = None
        self.clickNode = None
        self.clickRay = None
        self.buttonThrower.removeNode()
        self.buttonThrower = None
        self.inputDevice = None
        self.mouseWatcherNp.removeNode()
        self.mouseWatcherNp = None
        self.mouseWatcher = None
        self.mouseAndKeyboard.removeNode()
        self.mouseAndKeyboard = None
        self.win.removeAllDisplayRegions()
        self.displayRegion = None
        base.graphicsEngine.removeWindow(self.win)
        self.win = None

        self.camera2d.removeNode()
        self.camera2d = None
        self.cam2d = None

        self.render2d.removeNode()
        self.render2d = None

        self.a2dBackground = None
        self.a2dTop = None
        self.a2dBottom = None
        self.a2dLeft = None
        self.a2dRight = None
        self.aspect2d = None
        self.a2dTopCenter = None
        self.a2dTopCenterNs = None
        self.a2dBottomCenter = None
        self.a2dBottomCenterNs = None
        self.a2dLeftCenter = None
        self.a2dLeftCenterNs = None
        self.a2dRightCenter = None
        self.a2dRightCenterNs = None

        self.a2dTopLeft = None
        self.a2dTopLeftNs = None
        self.a2dTopRight = None
        self.a2dTopRightNs = None
        self.a2dBottomLeft = None
        self.a2dBottomLeftNs = None
        self.a2dBottomRight = None
        self.a2dBottomRightNs = None
        self.__oldAspectRatio = None

        self.qtWindow.deleteLater()
        self.qtWidget.deleteLater()
        self.qtWindow = None
        self.qtWidget = None

        self.deleteLater()

    def keyPressEvent(self, event):
        button = LEUtils.keyboardButtonFromQtKey(event.key())
        if button:
            self.inputDevice.buttonDown(button)

    def keyReleaseEvent(self, event):
        button = LEUtils.keyboardButtonFromQtKey(event.key())
        if button:
            self.inputDevice.buttonUp(button)

    def enterEvent(self, event):
        # Give ourselves focus.
        self.setFocus()
        QtWidgets.QWidget.enterEvent(self, event)

    def mouseMoveEvent(self, event):
        self.inputDevice.setPointerInWindow(event.pos().x(), event.pos().y())
        QtWidgets.QWidget.mouseMoveEvent(self, event)

    def leaveEvent(self, event):
        self.clearFocus()
        self.inputDevice.setPointerOutOfWindow()
        self.inputDevice.focusLost()
        QtWidgets.QWidget.leaveEvent(self, event)

    def mousePressEvent(self, event):
        btn = event.button()
        if btn == QtCore.Qt.LeftButton:
            self.inputDevice.buttonDown(MouseButton.one())
        elif btn == QtCore.Qt.MiddleButton:
            self.inputDevice.buttonDown(MouseButton.two())
        elif btn == QtCore.Qt.RightButton:
            self.inputDevice.buttonDown(MouseButton.three())
        QtWidgets.QWidget.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        btn = event.button()
        if btn == QtCore.Qt.LeftButton:
            self.inputDevice.buttonUp(MouseButton.one())
        elif btn == QtCore.Qt.MiddleButton:
            self.inputDevice.buttonUp(MouseButton.two())
        elif btn == QtCore.Qt.RightButton:
            self.inputDevice.buttonUp(MouseButton.three())
        QtWidgets.QWidget.mouseReleaseEvent(self, event)

    def wheelEvent(self, event):
        ang = event.angleDelta().y()
        if ang > 0:
            self.inputDevice.buttonDown(MouseButton.wheelUp())
            self.inputDevice.buttonUp(MouseButton.wheelUp())
        else:
            self.inputDevice.buttonDown(MouseButton.wheelDown())
            self.inputDevice.buttonUp(MouseButton.wheelDown())
        QtWidgets.QWidget.wheelEvent(self, event)

    def getAspectRatio(self):
        return self.win.getXSize() / self.win.getYSize()

    def setupRender2d(self):
        ## This is the root of the 2-D scene graph.
        self.render2d = NodePath("viewport-render2d")

        # Set up some overrides to turn off certain properties which
        # we probably won't need for 2-d objects.

        # It's probably important to turn off the depth test, since
        # many 2-d objects will be drawn over each other without
        # regard to depth position.

        # We used to avoid clearing the depth buffer before drawing
        # render2d, but nowadays we clear it anyway, since we
        # occasionally want to put 3-d geometry under render2d, and
        # it's simplest (and seems to be easier on graphics drivers)
        # if the 2-d scene has been cleared first.

        self.render2d.setDepthTest(0)
        self.render2d.setDepthWrite(0)
        self.render2d.setMaterialOff(1)
        self.render2d.setTwoSided(1)

        self.aspect2d = self.render2d.attachNewNode("viewport-aspect2d")

        aspectRatio = self.getAspectRatio()
        self.aspect2d.setScale(1.0 / aspectRatio, 1.0, 1.0)

        self.a2dBackground = self.aspect2d.attachNewNode("a2dBackground")

        ## The Z position of the top border of the aspect2d screen.
        self.a2dTop = 1.0
        ## The Z position of the bottom border of the aspect2d screen.
        self.a2dBottom = -1.0
        ## The X position of the left border of the aspect2d screen.
        self.a2dLeft = -aspectRatio
        ## The X position of the right border of the aspect2d screen.
        self.a2dRight = aspectRatio

        self.a2dTopCenter = self.aspect2d.attachNewNode("a2dTopCenter")
        self.a2dTopCenterNs = self.aspect2d.attachNewNode("a2dTopCenterNS")
        self.a2dBottomCenter = self.aspect2d.attachNewNode("a2dBottomCenter")
        self.a2dBottomCenterNs = self.aspect2d.attachNewNode("a2dBottomCenterNS")
        self.a2dLeftCenter = self.aspect2d.attachNewNode("a2dLeftCenter")
        self.a2dLeftCenterNs = self.aspect2d.attachNewNode("a2dLeftCenterNS")
        self.a2dRightCenter = self.aspect2d.attachNewNode("a2dRightCenter")
        self.a2dRightCenterNs = self.aspect2d.attachNewNode("a2dRightCenterNS")

        self.a2dTopLeft = self.aspect2d.attachNewNode("a2dTopLeft")
        self.a2dTopLeftNs = self.aspect2d.attachNewNode("a2dTopLeftNS")
        self.a2dTopRight = self.aspect2d.attachNewNode("a2dTopRight")
        self.a2dTopRightNs = self.aspect2d.attachNewNode("a2dTopRightNS")
        self.a2dBottomLeft = self.aspect2d.attachNewNode("a2dBottomLeft")
        self.a2dBottomLeftNs = self.aspect2d.attachNewNode("a2dBottomLeftNS")
        self.a2dBottomRight = self.aspect2d.attachNewNode("a2dBottomRight")
        self.a2dBottomRightNs = self.aspect2d.attachNewNode("a2dBottomRightNS")

        # Put the nodes in their places
        self.a2dTopCenter.setPos(0, 0, self.a2dTop)
        self.a2dTopCenterNs.setPos(0, 0, self.a2dTop)
        self.a2dBottomCenter.setPos(0, 0, self.a2dBottom)
        self.a2dBottomCenterNs.setPos(0, 0, self.a2dBottom)
        self.a2dLeftCenter.setPos(self.a2dLeft, 0, 0)
        self.a2dLeftCenterNs.setPos(self.a2dLeft, 0, 0)
        self.a2dRightCenter.setPos(self.a2dRight, 0, 0)
        self.a2dRightCenterNs.setPos(self.a2dRight, 0, 0)

        self.a2dTopLeft.setPos(self.a2dLeft, 0, self.a2dTop)
        self.a2dTopLeftNs.setPos(self.a2dLeft, 0, self.a2dTop)
        self.a2dTopRight.setPos(self.a2dRight, 0, self.a2dTop)
        self.a2dTopRightNs.setPos(self.a2dRight, 0, self.a2dTop)
        self.a2dBottomLeft.setPos(self.a2dLeft, 0, self.a2dBottom)
        self.a2dBottomLeftNs.setPos(self.a2dLeft, 0, self.a2dBottom)
        self.a2dBottomRight.setPos(self.a2dRight, 0, self.a2dBottom)
        self.a2dBottomRightNs.setPos(self.a2dRight, 0, self.a2dBottom)

    def setupCamera2d(self, sort = 10, displayRegion = (0, 1, 0, 1),
                      coords = (-1, 1, -1, 1)):
        dr = self.win.makeMonoDisplayRegion(*displayRegion)
        dr.setSort(10)

        # Enable clearing of the depth buffer on this new display
        # region (see the comment in setupRender2d, above).
        dr.setClearDepthActive(1)

        # Make any texture reloads on the gui come up immediately.
        dr.setIncompleteRender(False)

        left, right, bottom, top = coords

        # Now make a new Camera node.
        cam2dNode = Camera('cam2d')

        lens = OrthographicLens()
        lens.setFilmSize(right - left, top - bottom)
        lens.setFilmOffset((right + left) * 0.5, (top + bottom) * 0.5)
        lens.setNearFar(-1000, 1000)
        cam2dNode.setLens(lens)

        # self.camera2d is the analog of self.camera, although it's
        # not as clear how useful it is.
        self.camera2d = self.render2d.attachNewNode('camera2d')

        camera2d = self.camera2d.attachNewNode(cam2dNode)
        dr.setCamera(camera2d)

        self.cam2d = camera2d

        return camera2d

    def mouse1Up(self):
        pass

    def mouse1Down(self):
        pass

    def mouse2Up(self):
        pass

    def mouse2Down(self):
        pass

    def mouse3Up(self):
        pass

    def mouse3Down(self):
        pass

    def mouseEnter(self):
        self.updateView()

    def mouseExit(self):
        pass

    def mouseMove(self):
        pass

    def wheelUp(self):
        pass

    def wheelDown(self):
        pass

    def shouldRender(self):
        if not self.enabled:
            return False

        now = globalClock.getRealTime()
        if self.lastRenderTime != 0:
            elapsed = now - self.lastRenderTime
            if elapsed <= 0:
                return False

            frameRate = 1 / elapsed
            if frameRate > 100.0:
                # Never render faster than 100Hz
                return False

        return self.needsUpdate

    def renderView(self):
        self.lastRenderTime = globalClock.getRealTime()
        self.needsUpdate = False
        #self.win.setActive(1)
        base.requestRender()

    def tick(self):
        if self.shouldRender():
            self.renderView()
        else:
            pass
            #self.win.setActive(0)

    def getViewportName(self):
        return self.spec.name

    def getViewportCenterPixels(self):
        return LPoint2i(self.win.getXSize() // 2, self.win.getYSize() // 2)

    def centerCursor(self, cursor):
        center = self.getViewportCenterPixels()
        cursor.setPos(self.mapToGlobal(QtCore.QPoint(self.width() / 2, self.height() / 2)))
        self.inputDevice.setPointerInWindow(center.x, center.y)

    def viewportToWorld(self, viewport, vec = False):
        front = Point3()
        back = Point3()
        self.lens.extrude(viewport, front, back)
        world = (front + back) / 2

        worldMat = self.cam.getMat(render)
        if vec:
            world = worldMat.xformVec(world)
        else:
            world = worldMat.xformPoint(world)

        return world

    def worldToViewport(self, world):
        # move into local camera space
        invMat = Mat4(self.cam.getMat(render))
        invMat.invertInPlace()

        local = invMat.xformPoint(world)

        point = Point2()
        self.lens.project(local, point)

        return point

    def zeroUnusedCoordinate(self, vec):
        pass

    def click(self, mask, queue = None, traverser = None, root = None):
        if not self.mouseWatcher.hasMouse():
            return None

        if not queue:
            queue = self.clickQueue

        self.clickRay.setFromLens(self.camNode, self.mouseWatcher.getMouse())
        self.clickNode.setFromCollideMask(mask)
        self.clickNode.setIntoCollideMask(BitMask32.allOff())
        self.clickNp.reparentTo(self.cam)
        queue.clearEntries()
        if not traverser:
            base.clickTraverse(self.clickNp, queue)
        else:
            if not root:
                root = self.doc.render
            traverser.addCollider(self.clickNp, queue)
            traverser.traverse(root)
            traverser.removeCollider(self.clickNp)
        queue.sortEntries()
        self.clickNp.reparentTo(NodePath())

        return queue.getEntries()

    def fixRatio(self, size = None):
        if not self.lens:
            return

        if size is None:
            aspectRatio = self.win.getXSize() / self.win.getYSize()
        else:
            if size.y > 0:
                aspectRatio = size.x / size.y
            else:
                aspectRatio = 1.0

        if self.is2D():
            zoomFactor = (1.0 / self.zoom) * 100.0
            self.lens.setFilmSize(zoomFactor * aspectRatio, zoomFactor)
        else:
            self.lens.setAspectRatio(aspectRatio)

        if aspectRatio != self.__oldAspectRatio:
            self.__oldAspectRatio = aspectRatio
            # Fix up some anything that depends on the aspectRatio
            if aspectRatio < 1:
                # If the window is TALL, lets expand the top and bottom
                self.aspect2d.setScale(1.0, aspectRatio, aspectRatio)
                self.a2dTop = 1.0 / aspectRatio
                self.a2dBottom = - 1.0 / aspectRatio
                self.a2dLeft = -1
                self.a2dRight = 1.0
            else:
                # If the window is WIDE, lets expand the left and right
                self.aspect2d.setScale(1.0 / aspectRatio, 1.0, 1.0)
                self.a2dTop = 1.0
                self.a2dBottom = -1.0
                self.a2dLeft = -aspectRatio
                self.a2dRight = aspectRatio

            # Reposition the aspect2d marker nodes
            self.a2dTopCenter.setPos(0, 0, self.a2dTop)
            self.a2dTopCenterNs.setPos(0, 0, self.a2dTop)
            self.a2dBottomCenter.setPos(0, 0, self.a2dBottom)
            self.a2dBottomCenterNs.setPos(0, 0, self.a2dBottom)
            self.a2dLeftCenter.setPos(self.a2dLeft, 0, 0)
            self.a2dLeftCenterNs.setPos(self.a2dLeft, 0, 0)
            self.a2dRightCenter.setPos(self.a2dRight, 0, 0)
            self.a2dRightCenterNs.setPos(self.a2dRight, 0, 0)

            self.a2dTopLeft.setPos(self.a2dLeft, 0, self.a2dTop)
            self.a2dTopLeftNs.setPos(self.a2dLeft, 0, self.a2dTop)
            self.a2dTopRight.setPos(self.a2dRight, 0, self.a2dTop)
            self.a2dTopRightNs.setPos(self.a2dRight, 0, self.a2dTop)
            self.a2dBottomLeft.setPos(self.a2dLeft, 0, self.a2dBottom)
            self.a2dBottomLeftNs.setPos(self.a2dLeft, 0, self.a2dBottom)
            self.a2dBottomRight.setPos(self.a2dRight, 0, self.a2dBottom)
            self.a2dBottomRightNs.setPos(self.a2dRight, 0, self.a2dBottom)

    def resizeEvent(self, event):
        if not self.win:
            return

        newsize = LVector2i(event.size().width(), event.size().height())
        self.qtWidget.resize(newsize[0], newsize[1])
        self.qtWidget.move(0, 0)

        #props = WindowProperties()
        #props.setSize(newsize)
        #props.setOrigin(0, 0)
        #self.win.requestProperties(props)

        self.fixRatio(newsize)

        self.onResize(newsize)

        self.updateView()

    def onResize(self, newsize):
        pass

    def draw(self):
        pass

    def enable(self):
        # Render to the viewport
        self.win.setActive(True)
        self.enabled = True

    def disable(self):
        # Don't render to the viewport
        self.win.setActive(False)
        self.enabled = False
