from panda3d.core import Point2, Vec3, Vec4, KeyboardButton, NodePath, LineSegs, MeshDrawer, BitMask32, Shader, Vec2
from panda3d.core import Geom, GeomNode, GeomVertexFormat, GeomLines, GeomVertexWriter, GeomVertexData, InternalName, Point3
from panda3d.core import TextNode

from .BaseTool import BaseTool, ToolUsage
from direct.directbase import DirectRender
from direct.foundry.Viewport2D import Viewport2D
from direct.foundry.ViewportType import *
from direct.foundry import LEGlobals
from direct.foundry import RenderModes
from direct.foundry.Handles import Handles, HandleType
from direct.foundry.Box import Box
from direct.foundry.Rect import Rect
from direct.foundry.GeomView import GeomView
from direct.foundry import LEGlobals
from direct.foundry import KeyBinds
from direct.foundry.KeyBind import KeyBind

from enum import IntEnum
import py_linq

from PyQt5 import QtCore

class BoxAction(IntEnum):
    ReadyToDraw = 0
    DownToDraw = 1
    Drawing = 2
    Drawn = 3
    ReadyToResize = 4
    DownToResize = 5
    Resizing = 6

class ResizeHandle(IntEnum):
    TopLeft = 0
    Top = 1
    TopRight = 2

    Left = 3
    Center = 4
    Right = 5

    BottomLeft = 6
    Bottom = 7
    BottomRight = 8

class BoxState:

    def __init__(self):
        self.activeViewport = None
        self.action = BoxAction.ReadyToDraw
        self.handle = ResizeHandle.Center
        self.boxStart = None
        self.boxEnd = None
        self.moveStart = None
        self.preTransformBoxStart = None
        self.preTransformBoxEnd = None
        self.clickStart = Point2(0, 0)

    def cleanup(self):
        self.activeViewport = None
        self.action = None
        self.handle = None
        self.boxStart = None
        self.boxEnd = None
        self.moveStart = None
        self.preTransformBoxEnd = None
        self.preTransformBoxStart = None
        self.clickStart = None

    def isValidAndApplicable(self, vp):
        return (self.action != BoxAction.DownToDraw and
                self.action != BoxAction.Drawing and
                self.action != BoxAction.DownToResize and
                self.action != BoxAction.Resizing or
                self.activeViewport == vp)

    def fixBoxBounds(self):
        if self.action != BoxAction.Drawing and self.action != BoxAction.Resizing:
            return
        if not isinstance(self.activeViewport, Viewport2D):
            return

        vp = self.activeViewport

        assert len(self.boxStart) == len(self.boxEnd), "This literally should not happen. (BoxTool)"
        for i in range(len(self.boxStart)):
            start = self.boxStart[i]
            end = self.boxEnd[i]
            if start > end:
                tmp = start
                self.boxStart[i] = end
                vec = Vec3(0, 0, 0)
                vec[i] = 1
                flat = vp.flatten(vec)
                # FIXME: There has to be a better way of doing this.
                if flat.x == 1:
                    self.swapHandle("Left", "Right")
                if flat.z == 1:
                    self.swapHandle("Top", "Bottom")

    def swapHandle(self, one, two):
        if one in self.handle.name:
            self.handle = ResizeHandle[self.handle.name.replace(one, two)]
        elif two in self.handle.name:
            self.handle = ResizeHandle[self.handle.name.replace(two, one)]

# We need this class for each 2D viewport since it has to render different things
class BoxToolViewport:

    def __init__(self, tool, vp):
        self.vp = vp
        self.tool = tool

        # Set up the resize handles for this 2d viewport
        squareHandles = Handles(HandleType.Square)
        squareHandles.np.setHpr(vp.getViewHpr())
        squareHandles.addView(
            GeomView.Triangles, vp.getViewportMask(),
            renderState = RenderModes.DoubleSidedNoZ())
        squareHandles.generateGeometry()
        self.handlesList = {
            HandleType.Square: squareHandles
        }

        self.handles = squareHandles

        # Measurement text
        ttext = TextNode("boxToolTopText")
        ttext.setAlign(TextNode.ABoxedCenter)
        self.topText = NodePath(ttext)
        self.topText.setHpr(vp.getViewHpr())
        self.topText.hide(~vp.getViewportMask())
        self.topText.setBin("fixed", LEGlobals.WidgetSort)
        self.topText.setDepthWrite(False)
        self.topText.setDepthTest(False)

        ltext = TextNode("boxToolLeftText")
        ltext.setAlign(TextNode.ABoxedRight)
        self.leftText = NodePath(ltext)
        self.leftText.setHpr(vp.getViewHpr())
        self.leftText.hide(~vp.getViewportMask())
        self.leftText.setBin("fixed", LEGlobals.WidgetSort)
        self.leftText.setDepthWrite(False)
        self.leftText.setDepthTest(False)

    def cleanup(self):
        self.vp = None
        self.tool = None
        for handle in self.handlesList.values():
            handle.cleanup()
        self.handles = None
        self.topText.removeNode()
        self.topText = None
        self.leftText.removeNode()
        self.leftText = None

    def updateHandles(self, handles):
        self.handles.setHandles(handles)

    def updateTextPosScale(self):
        start = self.vp.flatten(self.tool.state.boxStart)
        end = self.vp.flatten(self.tool.state.boxEnd)
        center = (start + end) / 2
        offset = 4 / self.vp.zoom
        scale = 3.25 / self.vp.zoom

        self.topText.setPos(self.vp.expand(Point3(center.x, 0, end.z + offset)))
        self.topText.setScale(scale)
        self.leftText.setPos(self.vp.expand(Point3(start.x - offset, 0, center.z)))
        self.leftText.setScale(scale)

    def updateText(self):
        start = self.vp.flatten(self.tool.state.boxStart)
        end = self.vp.flatten(self.tool.state.boxEnd)
        width = abs(end.x - start.x)
        height = abs(end.z - start.z)
        self.topText.node().setText("%.1f" % width)
        self.leftText.node().setText("%.1f" % height)

    def showText(self):
        self.topText.reparentTo(self.tool.doc.render)
        self.leftText.reparentTo(self.tool.doc.render)

    def hideText(self):
        self.topText.reparentTo(NodePath())
        self.leftText.reparentTo(NodePath())

    def showHandles(self):
        self.handles.np.reparentTo(self.tool.doc.render)

    def hideHandles(self):
        self.handles.np.reparentTo(NodePath())

class BoxTool(BaseTool):

    Name = "Box Tool"
    ToolTip = "Box Tool"
    Usage = ToolUsage.Both
    Draw3DBox = True

    CursorHandles = {
        ResizeHandle.TopLeft: QtCore.Qt.SizeFDiagCursor,
        ResizeHandle.BottomRight: QtCore.Qt.SizeFDiagCursor,

        ResizeHandle.TopRight: QtCore.Qt.SizeBDiagCursor,
        ResizeHandle.BottomLeft: QtCore.Qt.SizeBDiagCursor,

        ResizeHandle.Top: QtCore.Qt.SizeVerCursor,
        ResizeHandle.Bottom: QtCore.Qt.SizeVerCursor,

        ResizeHandle.Left: QtCore.Qt.SizeHorCursor,
        ResizeHandle.Right: QtCore.Qt.SizeHorCursor,

        ResizeHandle.Center: QtCore.Qt.SizeAllCursor
    }

    DrawActions = [
        BoxAction.Drawing,
        BoxAction.Drawn,
        BoxAction.ReadyToResize,
        BoxAction.DownToResize,
        BoxAction.Resizing
    ]

    @staticmethod
    def getProperBoxCoordinates(start, end):
        newStart = Point3(min(start[0], end[0]), min(start[1], end[1]), min(start[2], end[2]))
        newEnd = Point3(max(start[0], end[0]), max(start[1], end[1]), max(start[2], end[2]))
        return [newStart, newEnd]

    @staticmethod
    def handleHitTestPoint(hitX, hitY, testX, testY, hitbox):
        return (hitX >= testX - hitbox and hitX <= testX + hitbox and
            hitY >= testY - hitbox and hitY <= testY + hitbox)

    @staticmethod
    def getHandle(current, boxStart, boxEnd, hitbox, offset, zoom):
        offset /= zoom
        hitbox /= zoom
        start = Point3(min(boxStart[0], boxEnd[0]) - offset, 0, min(boxStart[2], boxEnd[2]) - offset)
        end = Point3(max(boxStart[0], boxEnd[0]) + offset, 0, max(boxStart[2], boxEnd[2]) + offset)
        center = (end + start) / 2

        if BoxTool.handleHitTestPoint(current[0], current[2], start[0], start[2], hitbox):
            return ResizeHandle.BottomLeft

        if BoxTool.handleHitTestPoint(current[0], current[2], end[0], start[2], hitbox):
            return ResizeHandle.BottomRight

        if BoxTool.handleHitTestPoint(current[0], current[2], start[0], end[2], hitbox):
            return ResizeHandle.TopLeft

        if BoxTool.handleHitTestPoint(current[0], current[2], end[0], end[2], hitbox):
            return ResizeHandle.TopRight

        if BoxTool.handleHitTestPoint(current[0], current[2], center[0], start[2], hitbox):
            return ResizeHandle.Bottom

        if BoxTool.handleHitTestPoint(current[0], current[2], center[0], end[2], hitbox):
            return ResizeHandle.Top

        if BoxTool.handleHitTestPoint(current[0], current[2], start[0], center[2], hitbox):
            return ResizeHandle.Left

        if BoxTool.handleHitTestPoint(current[0], current[2], end[0], center[2], hitbox):
            return ResizeHandle.Right

        # Remove the offset padding for testing if we are inside the box itself
        start[0] += offset
        start[2] += offset
        end[0] -= offset
        end[2] -= offset

        if current[0] > start[0] and current[0] < end[0] \
            and current[2] > start[2] and current[2] < end[2]:
            return ResizeHandle.Center

        return None

    def __init__(self, mgr):
        BaseTool.__init__(self, mgr)
        self.handleWidth = 0.9
        self.handleOffset = 1.6
        self.handleType = HandleType.Square
        self.state = BoxState()
        self.suppressBox = False

        self.vps = []
        for vp in self.doc.viewportMgr.viewports:
            if vp.is2D():
                self.vps.append(BoxToolViewport(self, vp))

        # Representation of the box we are drawing
        self.box = Box()
        if self.Draw3DBox:
            # Render as solid lines in 3D viewport
            self.box.addView(GeomView.Lines, VIEWPORT_3D_MASK)
        # Render as dashed lines in 2D viewports
        self.box.addView(GeomView.Lines, VIEWPORT_2D_MASK, state = RenderModes.DashedLineNoZ())
        self.box.generateGeometry()
        self.box.np.setLightOff(1)
        self.box.np.setFogOff(1)
        self.box.np.hide(DirectRender.ShadowCameraBitmask | DirectRender.ReflectionCameraBitmask)

    def cleanup(self):
        self.handleWidth = None
        self.handleOffset = None
        self.handleType = None
        self.state.cleanup()
        self.state = None
        self.suppressBox = None
        for vp in self.vps:
            vp.cleanup()
        self.vps = None
        self.box.cleanup()
        self.box = None
        BaseTool.cleanup(self)

    def showHandles(self):
        for vp in self.vps:
            vp.showHandles()

    def hideHandles(self):
        for vp in self.vps:
            vp.hideHandles()

    def hideText(self):
        for vp in self.vps:
            vp.hideText()

    def showText(self):
        for vp in self.vps:
            vp.showText()

    def showBox(self):
        self.box.np.reparentTo(self.doc.render)

    def hideBox(self):
        self.box.np.reparentTo(NodePath())

    def updateHandles(self, vp):
        start = vp.vp.flatten(self.state.boxStart)
        end = vp.vp.flatten(self.state.boxEnd)
        handles = self.getHandles(start, end, vp.vp.zoom)
        vp.handles.setHandles(handles, vp.vp.zoom)

    def onBoxChanged(self):
        self.state.fixBoxBounds()

        if self.state.action in [BoxAction.Drawing, BoxAction.Resizing, BoxAction.Drawn]:
            # Fix up the text
            for vp in self.vps:
                vp.updateText()
                self.updateHandles(vp)
            self.box.setMinMax(self.state.boxStart, self.state.boxEnd)

        self.doc.updateAllViews()

        # TODO: mediator.selectionBoxChanged

    def activate(self):
        BaseTool.activate(self)
        self.accept('mouse1', self.mouseDown)
        self.accept('mouse1-up', self.mouseUp)
        self.accept('mouseMoved', self.mouseMove)
        self.accept('mouseEnter', self.mouseEnter)
        self.accept('mouseExit', self.mouseExit)
        self.accept(KeyBinds.getPandaShortcut(KeyBind.Confirm), self.enterDown)
        self.accept(KeyBinds.getPandaShortcut(KeyBind.Cancel), self.escapeDown)

    def disable(self):
        BaseTool.disable(self)
        self.maybeCancel()

    def mouseDown(self):
        if self.suppressBox:
            return

        vp = base.viewportMgr.activeViewport
        if not vp:
            return
        if vp.is3D():
            self.mouseDown3D()
            return

        self.state.clickStart = Point2(vp.getMouse())

        if self.state.action in [BoxAction.ReadyToDraw, BoxAction.Drawn]:
            self.leftMouseDownToDraw()
        elif self.state.action == BoxAction.ReadyToResize:
            self.leftMouseDownToResize()

    def mouseDown3D(self):
        pass

    def leftMouseDownToDraw(self):
        self.hideText()
        self.hideBox()
        self.hideHandles()
        vp = base.viewportMgr.activeViewport
        mouse = vp.getMouse()
        self.state.activeViewport = vp
        self.state.action = BoxAction.DownToDraw
        toWorld = vp.viewportToWorld(mouse)
        expanded = vp.expand(toWorld)
        self.state.boxStart = base.snapToGrid(expanded)
        self.state.boxEnd = Point3(self.state.boxStart)
        self.state.handle = ResizeHandle.BottomLeft
        self.onBoxChanged()

    def leftMouseDownToResize(self):
        self.hideHandles()
        vp = base.viewportMgr.activeViewport
        self.state.action = BoxAction.DownToResize
        self.state.moveStart = vp.viewportToWorld(vp.getMouse())
        self.state.preTransformBoxStart = self.state.boxStart
        self.state.preTransformBoxEnd = self.state.boxEnd

    def mouseUp(self):
        vp = base.viewportMgr.activeViewport
        if not vp:
            return

        if vp.is3D():
            self.mouseUp3D()
            return

        if self.state.action == BoxAction.Drawing:
            self.leftMouseUpDrawing()
        elif self.state.action == BoxAction.Resizing:
            self.leftMouseUpResizing()
        elif self.state.action == BoxAction.DownToDraw:
            self.leftMouseClick()
        elif self.state.action == BoxAction.DownToResize:
            self.leftMouseClickOnResizeHandle()

    def mouseUp3D(self):
        pass

    def resizeBoxDone(self):
        vp = base.viewportMgr.activeViewport
        coords = self.getResizedBoxCoordinates(vp)
        corrected = BoxTool.getProperBoxCoordinates(coords[0], coords[1])
        self.state.activeViewport = None
        self.state.action = BoxAction.Drawn
        self.state.boxStart = corrected[0]
        self.state.boxEnd = corrected[1]
        self.showHandles()
        self.onBoxChanged()

    def leftMouseUpDrawing(self):
        self.resizeBoxDone()

    def leftMouseUpResizing(self):
        self.resizeBoxDone()

    def leftMouseClick(self):
        self.state.activeViewport = None
        self.state.action = BoxAction.ReadyToDraw
        self.state.boxStart = None
        self.state.boxEnd = None
        self.onBoxChanged()

    def leftMouseClickOnResizeHandle(self):
        self.state.action = BoxAction.ReadyToResize

    def mouseMove(self, vp):
        if vp.is3D():
            self.mouseMove3D()
            return
        if not self.state.isValidAndApplicable(vp):
            return

        if self.state.action in [BoxAction.Drawing, BoxAction.DownToDraw]:
            self.mouseDraggingToDraw()
        elif self.state.action in [BoxAction.Drawn, BoxAction.ReadyToResize]:
            self.mouseHoverWhenDrawn()
        elif self.state.action in [BoxAction.DownToResize, BoxAction.Resizing]:
            self.mouseDraggingToResize()

    def mouseMove3D(self):
        pass

    def resizeBoxDrag(self):
        vp = base.viewportMgr.activeViewport
        coords = self.getResizedBoxCoordinates(vp)
        self.state.boxStart = coords[0]
        self.state.boxEnd = coords[1]
        self.onBoxChanged()
        #render.ls()

    def mouseDraggingToDraw(self):
        self.showBox()
        self.showText()
        self.state.action = BoxAction.Drawing
        self.resizeBoxDrag()

    def mouseDraggingToResize(self):
        self.state.action = BoxAction.Resizing
        self.resizeBoxDrag()

    def cursorForHandle(self, handle):
        return self.CursorHandles.get(handle, QtCore.Qt.ArrowCursor)

    def resetCursor(self):
        vp = base.viewportMgr.activeViewport

    def mouseHoverWhenDrawn(self):
        vp = base.viewportMgr.activeViewport
        now = vp.viewportToWorld(vp.getMouse())
        start = vp.flatten(self.state.boxStart)
        end = vp.flatten(self.state.boxEnd)
        handle = BoxTool.getHandle(now, start, end, self.handleWidth, self.handleOffset, vp.zoom)
        if handle is not None and (handle == ResizeHandle.Center or self.filterHandle(handle)):
            vp.setCursor(self.cursorForHandle(handle))
            self.state.handle = handle
            self.state.action = BoxAction.ReadyToResize
            self.state.activeViewport = vp
        else:
            vp.setCursor(QtCore.Qt.ArrowCursor)
            self.state.action = BoxAction.Drawn
            self.state.activeViewport = None

    def getResizeOrigin(self, vp):
        if self.state.action != BoxAction.Resizing or self.state.handle != ResizeHandle.Center:
            return None
        st = vp.flatten(self.state.preTransformBoxStart)
        ed = vp.flatten(self.state.preTransformBoxEnd)
        points = [st, ed, Point3(st.x, 0, ed.z), Point3(ed.x, 0, st.z)]
        points.sort(key = lambda x: (self.state.moveStart - x).lengthSquared())
        return points[0]

    def getResizeDistance(self, vp):
        origin = self.getResizeOrigin(vp)
        if not origin:
            return None
        before = self.state.moveStart
        after = vp.viewportToWorld(vp.getMouse())
        return base.snapToGrid(origin + after - before) - origin

    def getResizedBoxCoordinates(self, vp):
        if self.state.action != BoxAction.Resizing and self.state.action != BoxAction.Drawing:
            return [self.state.boxStart, self.state.boxEnd]
        now = base.snapToGrid(vp.viewportToWorld(vp.getMouse()))
        cstart = vp.flatten(self.state.boxStart)
        cend = vp.flatten(self.state.boxEnd)

        # Proportional scaling
        ostart = vp.flatten(self.state.preTransformBoxStart if self.state.preTransformBoxStart else Vec3.zero())
        oend = vp.flatten(self.state.preTransformBoxEnd if self.state.preTransformBoxEnd else Vec3.zero())
        owidth = oend.x - ostart.x
        oheight = oend.z - ostart.z
        proportional = vp.mouseWatcher.isButtonDown(KeyboardButton.control()) and \
            self.state.action == BoxAction.Resizing and owidth != 0 and oheight != 0

        if self.state.handle == ResizeHandle.TopLeft:
            cstart.x = now.x
            cend.z = now.z
        elif self.state.handle == ResizeHandle.Top:
            cend.z = now.z
        elif self.state.handle == ResizeHandle.TopRight:
            cend.x = now.x
            cend.z = now.z
        elif self.state.handle == ResizeHandle.Left:
            cstart.x = now.x
        elif self.state.handle == ResizeHandle.Center:
            cdiff = cend - cstart
            distance = self.getResizeDistance(vp)
            if not distance:
                cstart = vp.flatten(self.state.preTransformBoxStart) + now \
                    - base.snapToGrid(self.state.moveStart)
            else:
                cstart = vp.flatten(self.state.preTransformBoxStart) + distance
            cend = cstart + cdiff
        elif self.state.handle == ResizeHandle.Right:
            cend.x = now.x
        elif self.state.handle == ResizeHandle.BottomLeft:
            cstart.x = now.x
            cstart.z = now.z
        elif self.state.handle == ResizeHandle.Bottom:
            cstart.z = now.z
        elif self.state.handle == ResizeHandle.BottomRight:
            cend.x = now.x
            cstart.z = now.z

        if proportional:
            nwidth = cend.x - cstart.x
            nheight = cend.z - cstart.z
            mult = max(nwidth / owidth, nheight / oheight)
            pwidth = owidth * mult
            pheight = oheight * mult
            wdiff = pwidth - nwidth
            hdiff = pheight - nheight
            if self.state.handle == ResizeHandle.TopLeft:
                cstart.x -= wdiff
                cend.z += hdiff
            elif self.state.handle == ResizeHandle.TopRight:
                cend.x += wdiff
                cend.z += hdiff
            elif self.state.handle == ResizeHandle.BottomLeft:
                cstart.x -= wdiff
                cstart.z -= hdiff
            elif self.state.handle == ResizeHandle.BottomRight:
                cend.x += wdiff
                cstart.z -= hdiff

        cstart = vp.expand(cstart) + vp.getUnusedCoordinate(self.state.boxStart)
        cend = vp.expand(cend) + vp.getUnusedCoordinate(self.state.boxEnd)
        return [cstart, cend]

    def maybeCancel(self):
        if self.state.action in [BoxAction.ReadyToDraw, BoxAction.DownToDraw]:
            return False
        if self.state.activeViewport:
            self.state.activeViewport.setCursor(QtCore.Qt.ArrowCursor)
            self.state.activeViewport = None
        self.state.action = BoxAction.ReadyToDraw
        self.hideText()
        self.hideBox()
        self.hideHandles()
        return True

    def enterDown(self):
        if self.maybeCancel():
            self.boxDrawnConfirm()

    def escapeDown(self):
        if self.maybeCancel():
            self.boxDrawnCancel()

    def boxDrawnConfirm(self):
        pass

    def boxDrawnCancel(self):
        pass

    def mouseEnter(self, vp):
        if self.state.activeViewport:
            self.state.activeViewport.setCursor(QtCore.Qt.ArrowCursor)

    def mouseExit(self, vp):
        if self.state.activeViewport:
            self.state.activeViewport.setCursor(QtCore.Qt.ArrowCursor)

    def getHandles(self, start, end, zoom, offset = None):
        if offset is None:
            offset = self.handleOffset

        half = (end - start) / 2
        dist = offset / zoom

        return py_linq.Enumerable([
            (ResizeHandle.TopLeft, start.x - dist, end.z + dist),
            (ResizeHandle.TopRight, end.x + dist, end.z + dist),
            (ResizeHandle.BottomLeft, start.x - dist, start.z - dist),
            (ResizeHandle.BottomRight, end.x + dist, start.z - dist),

            (ResizeHandle.Top, start.x + half.x, end.z + dist),
            (ResizeHandle.Left, start.x - dist, start.z + half.z),
            (ResizeHandle.Right, end.x + dist, start.z + half.z),
            (ResizeHandle.Bottom, start.x + half.x, start.z - dist)
        ]).where(lambda x: self.filterHandle(x[0])) \
            .select(lambda x: Point3(x[1], 0, x[2])) \
            .to_list()

    def filterHandle(self, handle):
        return True

    def moveBox(self, pos):
        currPos = (self.state.boxStart + self.state.boxEnd) / 2.0
        delta = pos - currPos
        self.state.boxStart += delta
        self.state.boxEnd += delta
        self.state.action = BoxAction.Drawn
        self.resizeBoxDone()

    #def scaleBox(self, scale,):
    #    self.state.boxStart.componentwiseMult(scale)
    #    self.state.boxEnd.componentwiseMult(scale)
    #    self.state.action = BoxAction.Drawn
    #    self.resizeBoxDone()

    def update(self):
        for vp in self.vps:
            if self.state.action != BoxAction.ReadyToDraw:
                vp.updateTextPosScale()
            if self.state.action in [BoxAction.ReadyToResize, BoxAction.Drawn]:
                self.updateHandles(vp)

    def getSelectionBox(self):
        # Return a min/max point for a box that can be used
        # for selection.
        #
        # If one of the dimensions has a depth value of 0, extend it out into
        # infinite space.
        # If two or more dimensions have depth 0, do nothing.

        sameX = self.state.boxStart.x == self.state.boxEnd.x
        sameY = self.state.boxStart.y == self.state.boxEnd.y
        sameZ = self.state.boxStart.z == self.state.boxEnd.z
        start = Vec3(self.state.boxStart)
        end = Vec3(self.state.boxEnd)
        invalid = False

        inf = 99999999.0
        negInf = -99999999.0

        if sameX:
            if sameY or sameZ:
                invalid = True
            start.x = negInf
            end.x = inf

        if sameY:
            if sameZ:
                invalid = True
            start.y = negInf
            end.y = inf

        if sameZ:
            start.z = negInf
            end.z = inf

        return [invalid, start, end]
