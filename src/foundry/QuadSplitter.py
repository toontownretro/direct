# Filename: QuadSplitter.py
# Created by:  Brian Lach (June 4, 2020)
# Purpose: Resizable quad-viewport widget for PyQt. Ported to Python.

from direct.directnotify.DirectNotifyGlobal import directNotify

from PyQt5 import QtWidgets, QtCore

import math

class AdvSplitter(QtWidgets.QWidget):

    def __init__(self, parent, splitter, orientation):
        QtWidgets.QWidget.__init__(self, parent)
        self._percent = 0.5
        self.orientation = orientation
        self.mouse = False
        self.center = False
        self.splitter = splitter

        self.mousePos = QtCore.QPoint(0, 0)

        self.setMouseTracking(True)
        if orientation == QtCore.Qt.Horizontal:
            self.setCursor(QtCore.Qt.SplitHCursor)
        elif orientation == QtCore.Qt.Vertical:
            self.setCursor(QtCore.Qt.SplitVCursor)

    def cleanup(self):
        self._percent = None
        self.orientation = None
        self.mouse = None
        self.center = None
        self.splitter = None
        self.mousePos = None
        self.deleteLater()

    def percent(self):
        return self._percent

    def setPercent(self, val):
        self._percent = val

    def paintEvent(self, event):
        painter = QtWidgets.QStylePainter(self)
        opt1 = QtWidgets.QStyleOption()
        opt2 = QtWidgets.QStyleOption()
        opt1.initFrom(self)
        opt2.initFrom(self)

        # opt1
        opt1.state = opt2.state = QtWidgets.QStyle.State_Raised
        if (self.orientation == QtCore.Qt.Horizontal):
            opt1.state |= QtWidgets.QStyle.State_Horizontal
            opt2.state |= QtWidgets.QStyle.State_Horizontal
            if self.splitter:
                hiPart = math.floor(opt1.rect.height() * self.splitter.realPercent(QtCore.Qt.Vertical) + 0.5)
                loPart = opt1.rect.height() - hiPart
                opt1.rect.setBottom(opt1.rect.top() + hiPart)
                opt2.rect.setTop(opt2.rect.bottom() - loPart)
        elif self.splitter:
            hiPart = math.floor(opt1.rect.width() * self.splitter.realPercent(QtCore.Qt.Horizontal) + 0.5)
            loPart = opt1.rect.width() - hiPart
            opt1.rect.setRight(opt1.rect.left() + hiPart)
            opt2.rect.setLeft(opt2.rect.right() - loPart)

        painter.drawControl(QtWidgets.QStyle.CE_Splitter, opt1)
        if self.splitter:
            painter.drawControl(QtWidgets.QStyle.CE_Splitter, opt2)

        painter.end()

    def mouseMoveEvent(self, event):
        if (not self.mouse) and self.splitter:
            if self.orientation == QtCore.Qt.Horizontal:
                hiPart = math.floor(self.height() * self.splitter.realPercent(QtCore.Qt.Vertical) + 0.5)
                if ((event.pos().y() > (hiPart - self.splitter.centerPartWidth() / 2)) and
                    (event.pos().y() < (hiPart + self.splitter.centerPartWidth() / 2))):
                    self.setCursor(QtCore.Qt.SizeAllCursor)
                else:
                    self.setCursor(QtCore.Qt.SplitHCursor)
            else:
                hiPart = math.floor(self.width() * self.splitter.realPercent(QtCore.Qt.Horizontal) + 0.5)
                if ((event.pos().x() > (hiPart - self.splitter.centerPartWidth() / 2)) and
                    (event.pos().x() < (hiPart + self.splitter.centerPartWidth() / 2))):
                    self.setCursor(QtCore.Qt.SizeAllCursor)
                else:
                    self.setCursor(QtCore.Qt.SplitVCursor)
        elif self.center:
            if self.cursor().shape() != QtCore.Qt.SizeAllCursor:
                self.setCursor(QtCore.Qt.SizeAllCursor)
        elif self.orientation == QtCore.Qt.Horizontal:
            if self.cursor().shape() != QtCore.Qt.SplitHCursor:
                self.setCursor(QtCore.Qt.SplitHCursor)
        elif self.cursor().shape() != QtCore.Qt.SplitVCursor:
            self.setCursor(QtCore.Qt.SplitVCursor)

        if self.mouse and (event.buttons() & QtCore.Qt.LeftButton):
            pt = self.mapToParent(event.pos())
            if isinstance(self.parent(), QuadSplitter):
                self.parent().splitterMove(self, pt - self.mousePos, self.center)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.mouse = True
            if self.splitter:
                if self.orientation == QtCore.Qt.Horizontal:
                    hiPart = math.floor(self.height() * self.splitter.realPercent(QtCore.Qt.Vertical) + 0.5)
                    if ((event.pos().y() > (hiPart - self.splitter.centerPartWidth() / 2)) and
                        (event.pos().y() < (hiPart + self.splitter.centerPartWidth() / 2))):
                        self.center = True
                        self.setCursor(QtCore.Qt.SizeAllCursor)
                    else:
                        self.setCursor(QtCore.Qt.SplitHCursor)
                else:
                    hiPart = math.floor(self.width() * self.splitter.realPercent(QtCore.Qt.Horizontal) + 0.5)
                    if ((event.pos().x() > (hiPart - self.splitter.centerPartWidth() / 2)) and
                        (event.pos().x() < (hiPart + self.splitter.centerPartWidth() / 2))):
                        self.center = True
                        self.setCursor(QtCore.Qt.SizeAllCursor)
                    else:
                        self.setCursor(QtCore.Qt.SplitVCursor)

        self.mousePos = self.mapToParent(event.pos())
        if isinstance(self.parent(), QuadSplitter):
            self.parent().splitterMoveStart(self, self.center)

    def mouseReleaseEvent(self, event):
        self.mouse = False
        self.center = False

class QuadSplitter(QtWidgets.QFrame):
    notify = directNotify.newCategory("QuadSplitter")

    def __init__(self, parent = None):
        QtWidgets.QFrame.__init__(self, parent)
        self.grid = [[None, None], [None, None]]
        self.minimumWidgetSize = 30
        self.centerPart = 30
        self.spacing = 5
        self.splittersSpacing = 5
        self.horizontalSplitter = AdvSplitter(self, self, QtCore.Qt.Horizontal)
        self.verticalSplitter = AdvSplitter(self, self, QtCore.Qt.Vertical)
        self.splittersMovingPos = QtCore.QPoint(0, 0)
        self.arrange()

    def cleanup(self):
        self.grid = None
        self.minimumWidgetSize = None
        self.centerPart = None
        self.spacing = None
        self.splittersSpacing = None
        self.horizontalSplitter.cleanup()
        self.horizontalSplitter = None
        self.verticalSplitter.cleanup()
        self.verticalSplitter = None
        self.splittersMovingPos = None
        self.deleteLater()

    def resizeEvent(self, event):
        self.arrange()

    def centerPartWidth(self):
        return self.centerPart

    def addWidget(self, widget, row, column):
        if row < 0 or column < 0 or row > 1 or column > 1:
            self.notify.warning("Cannot add %s/%s to %s/%s at row %i column %i" % (
                widget.metaObject().className(), widget.objectName(),
                self.metaObject().className(), self.objectName(), row, column
            ))
            return

        needShow = self.isVisible() and \
            not (widget.isHidden() and widget.testAttribute(QtCore.Qt.WA_WState_ExplicitShowHide))
        if widget.parentWidget() != self:
            widget.setParent(self)
        if needShow:
            widget.show()

        self.grid[row][column] = widget

        self.arrange()

    def realPercent(self, orientation):
        if orientation == QtCore.Qt.Horizontal:
            newX = self.horizontalSplitter.x() - self.realSpacing()
            return newX / self.realWidth()

        newY = self.verticalSplitter.y() - self.realSpacing()
        return newY / self.realHeight()

    def realSpacing(self):
        return self.spacing + self.frameWidth()

    def realWidth(self):
        return self.width() - (self.realSpacing() * 2) - self.splittersSpacing

    def realHeight(self):
        return self.height() - (self.realSpacing() * 2) - self.splittersSpacing

    def arrange(self):
        minMaxHorizontalSizes = [[0, QtWidgets.QWIDGETSIZE_MAX], [0, QtWidgets.QWIDGETSIZE_MAX]]
        minMaxVerticalSizes = [[0, QtWidgets.QWIDGETSIZE_MAX], [0, QtWidgets.QWIDGETSIZE_MAX]]

        for r in range(2):
            for c in range(2):
                if (self.grid[r][c] is not None) and self.grid[r][c].parent() == self:
                    minMaxHorizontalSizes[c] = [
                        max(self.minimumWidgetSize if self.grid[r][c].minimumWidth() < self.minimumWidgetSize else self.grid[r][c].minimumWidth(),
                            minMaxHorizontalSizes[c][0]),
                        min(self.grid[r][c].maximumWidth(), minMaxHorizontalSizes[c][1])
                    ]

                    minMaxVerticalSizes[r] = [
                        max(self.minimumWidgetSize if self.grid[r][c].minimumHeight() < self.minimumWidgetSize else self.grid[r][c].minimumHeight(),
                            minMaxVerticalSizes[r][0]),
                        min(self.grid[r][c].maximumHeight(), minMaxVerticalSizes[r][1])
                    ]
                else:
                    self.grid[r][c] = None

        # columns
        leftColumnWidth = math.floor(self.realWidth() * self.horizontalSplitter.percent() + 0.5)
        if leftColumnWidth < minMaxHorizontalSizes[0][0]:
            leftColumnWidth = minMaxHorizontalSizes[0][0]
        if leftColumnWidth > minMaxHorizontalSizes[0][1]:
            leftColumnWidth = minMaxHorizontalSizes[0][1]

        columnWidth = leftColumnWidth

        rightColumnWidth = self.realWidth() - leftColumnWidth
        if rightColumnWidth < minMaxHorizontalSizes[1][0]:
            rightColumnWidth = minMaxHorizontalSizes[1][0]
            columnWidth = self.realWidth() - rightColumnWidth
        if rightColumnWidth > minMaxHorizontalSizes[1][1]:
            rightColumnWidth = minMaxHorizontalSizes[1][1]
            columnWidth = self.realWidth() - rightColumnWidth

        # rows
        topColumnHeight = math.floor(self.realHeight() * self.verticalSplitter.percent() + 0.5)
        if topColumnHeight < minMaxVerticalSizes[0][0]:
            topColumnHeight = minMaxVerticalSizes[0][0]
        if topColumnHeight > minMaxVerticalSizes[0][1]:
            topColumnHeight = minMaxVerticalSizes[0][1]

        columnHeight = topColumnHeight

        bottomColumnHeight = self.realHeight() - topColumnHeight
        if bottomColumnHeight < minMaxVerticalSizes[1][0]:
            bottomColumnHeight = minMaxVerticalSizes[1][0]
            columnHeight = self.realHeight() - bottomColumnHeight
        if bottomColumnHeight > minMaxVerticalSizes[1][1]:
            bottomColumnHeight = minMaxVerticalSizes[1][1]
            columnHeight = self.realHeight() - bottomColumnHeight

        self.horizontalSplitter.setGeometry(self.realSpacing() + columnWidth, self.realSpacing(),
            self.splittersSpacing, self.height() - self.realSpacing() * 2)
        self.horizontalSplitter.raise_()

        self.verticalSplitter.setGeometry(self.realSpacing(), self.realSpacing() + columnHeight,
            self.width() - self.realSpacing() * 2, self.splittersSpacing)
        self.verticalSplitter.raise_()

        if self.grid[0][0]:
            self.grid[0][0].setGeometry(self.realSpacing(), self.realSpacing(), columnWidth, columnHeight)
        if self.grid[0][1]:
            self.grid[0][1].setGeometry(self.realSpacing() + columnWidth + self.splittersSpacing, self.realSpacing(),
                self.realWidth() - columnWidth, columnHeight)

        if self.grid[1][0]:
            self.grid[1][0].setGeometry(self.realSpacing(), self.realSpacing() + columnHeight + self.splittersSpacing,
                columnWidth, self.realHeight() - columnHeight)
        if self.grid[1][1]:
            self.grid[1][1].setGeometry(self.realSpacing() + columnWidth + self.splittersSpacing,
                self.realSpacing() + columnHeight + self.splittersSpacing, self.realWidth() - columnWidth,
                self.realHeight() - columnHeight)

        #messenger.send('quadSplitterResized')

    def splitterMoveStart(self, splitter, center):
        self.splittersMovingPos = QtCore.QPoint(self.horizontalSplitter.x(), self.verticalSplitter.y())

    def splitterMove(self, splitter, offset, center):
        if center:
            newX = self.splittersMovingPos.x() + offset.x() - self.realSpacing()
            newY = self.splittersMovingPos.y() + offset.y() - self.realSpacing()
            self.horizontalSplitter.setPercent(newX / self.realWidth())
            self.verticalSplitter.setPercent(newY / self.realHeight())
        elif splitter == self.horizontalSplitter:
            newX = self.splittersMovingPos.x() + offset.x() - self.realSpacing()
            splitter.setPercent(newX / self.realWidth())
        else:
            newY = self.splittersMovingPos.y() + offset.y() - self.realSpacing()
            splitter.setPercent(newY / self.realHeight())

        self.arrange()
