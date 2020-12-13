from panda3d.core import Point3, Vec4

from .BoxTool import BoxTool
from .ToolOptions import ToolOptions
from direct.foundry.Create import MultiCreate
from direct.foundry.Select import Select, Deselect
from direct.foundry.ActionGroup import ActionGroup
from direct.foundry.ChangeSelectionMode import ChangeSelectionMode
from direct.foundry.SelectionType import SelectionType
from direct.foundry.GridSettings import GridSettings
from direct.foundry.KeyBind import KeyBind
from direct.foundry.IDGenerator import IDGenerator

from direct.foundry import MaterialPool, LEGlobals, LEConfig

from PyQt5 import QtWidgets, QtCore

class BlockToolOptions(ToolOptions):

    GlobalPtr = None
    @staticmethod
    def getGlobalPtr():
        self = BlockToolOptions
        if not self.GlobalPtr:
            self.GlobalPtr = BlockToolOptions()
        return self.GlobalPtr

    def __init__(self):
        ToolOptions.__init__(self)

        self.roundVertices = True

        shapeBase = QtWidgets.QWidget(self)
        self.layout().addWidget(shapeBase)
        shapeBase.setLayout(QtWidgets.QFormLayout())
        typeLbl = QtWidgets.QLabel("Shape:", shapeBase)
        self.typeCombo = QtWidgets.QComboBox(shapeBase)
        self.typeCombo.currentIndexChanged.connect(self.__selectBrush)
        shapeBase.layout().addRow(typeLbl, self.typeCombo)
        self.roundBox = QtWidgets.QCheckBox("Round created vertices", shapeBase)
        self.roundBox.setChecked(self.roundVertices)
        self.roundBox.stateChanged.connect(self.__changeRound)
        shapeBase.layout().addRow(None, self.roundBox)

        self.currentControls = None
        self.selectedBrush = base.brushMgr.brushes[0]

        for brush in base.brushMgr.brushes:
            self.typeCombo.addItem(brush.Name)

    def __changeRound(self, state):
        self.roundVertices = (state != QtCore.Qt.Unchecked)
        if self.tool:
            self.tool.maybeUpdatePreviewBrushes()

    def __selectBrush(self, index):
        if self.currentControls:
            self.layout().removeWidget(self.currentControls)
            self.currentControls.setParent(None)

        brush = base.brushMgr.brushes[index]
        self.selectedBrush = brush
        if len(brush.controls) > 0:
            self.currentControls = brush.controlsGroup
            self.layout().addWidget(self.currentControls)
        else:
            self.currentControls = None

        self.roundBox.setEnabled(self.selectedBrush.CanRound)

        if self.tool:
            self.tool.maybeUpdatePreviewBrushes()

class BlockTool(BoxTool):

    Name = "Block"
    KeyBind = KeyBind.BlockTool
    ToolTip = "Block tool"
    Icon = "icons/editor-block.png"
    Draw3DBox = False

    def __init__(self, mgr):
        BoxTool.__init__(self, mgr)
        self.box.setColor(LEGlobals.PreviewBrush2DColor)
        self.lastBox = None
        self.options = BlockToolOptions.getGlobalPtr()
        self.previewBrushes = []

    def activate(self):
        BoxTool.activate(self)
        self.acceptGlobal('brushValuesChanged', self.onBrushValuesChanged)

    def onBrushValuesChanged(self, brush):
        if brush == self.options.selectedBrush:
            self.maybeUpdatePreviewBrushes()

    def enable(self):
        BoxTool.enable(self)

        solids = []
        for sel in base.selectionMgr.selectedObjects:
            if sel.ObjectName == "solid":
                solids.append(sel)

        if len(solids) > 0:
            mins = Point3()
            maxs = Point3()
            solids[len(solids) - 1].np.calcTightBounds(mins, maxs, base.render)
            self.lastBox = [mins, maxs]
        elif self.lastBox is None:
            self.lastBox = [Point3(0), Point3(GridSettings.DefaultStep)]

    def disable(self):
        self.removePreviewBrushes()
        BoxTool.disable(self)

    def removePreviewBrushes(self):
        for brush in self.previewBrushes:
            brush.delete()
        self.previewBrushes = []

    def updatePreviewBrushes(self):
        self.removePreviewBrushes()

        self.previewBrushes = self.options.selectedBrush.create(IDGenerator(), self.state.boxStart,
            self.state.boxEnd, self.determineMaterial(), 2 if self.options.roundVertices else 0, True)

    def cleanup(self):
        self.lastBox = None
        self.previewBrushes = None
        BoxTool.cleanup(self)

    def leftMouseDownToDraw(self):
        BoxTool.leftMouseDownToDraw(self)

        vp = base.viewportMgr.activeViewport
        if self.lastBox is not None:
            self.state.boxStart += vp.getUnusedCoordinate(self.lastBox[0])
            self.state.boxEnd += vp.getUnusedCoordinate(self.lastBox[1])
        else:
            self.state.boxEnd += vp.getUnusedCoordinate(Point3(GridSettings.DefaultStep))

        self.onBoxChanged()

    def onBoxChanged(self):
        BoxTool.onBoxChanged(self)
        self.maybeUpdatePreviewBrushes()

    def maybeUpdatePreviewBrushes(self):
        if (not self.state.boxStart or not self.state.boxEnd) or \
        (self.state.boxStart[0] == self.state.boxEnd[0] or self.state.boxStart[1] == self.state.boxEnd[1]
            or self.state.boxStart[2] == self.state.boxEnd[2]):
            self.removePreviewBrushes()
            return

        self.updatePreviewBrushes()

        self.doc.updateAllViews()

    def determineMaterial(self):
        if MaterialPool.ActiveMaterial:
            return MaterialPool.ActiveMaterial
        else:
            return MaterialPool.getMaterial(LEConfig.default_material.getValue())

    def boxDrawnConfirm(self):
        self.removePreviewBrushes()

        box = [self.state.boxStart, self.state.boxEnd]
        if box[0].x != box[1].x and box[0].y != box[1].y and box[0].z != box[1].z:
            solids = self.options.selectedBrush.create(base.document.idGenerator, self.state.boxStart, self.state.boxEnd,
                self.determineMaterial(), 2)

            creations = []
            for solid in solids:
                creations.append((base.document.world.id, solid))
            base.actionMgr.performAction("Create %i solid(s)" % len(creations),
                ActionGroup([
                    Deselect(all = True),
                    MultiCreate(creations),
                    ChangeSelectionMode(SelectionType.Groups),
                    Select(solids, False)
                ])
            )

            self.lastBox = box

    def boxDrawnCancel(self):
        self.lastBox = [self.state.boxStart, self.state.boxEnd]
        self.removePreviewBrushes()
