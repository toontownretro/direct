from direct.showbase.DirectObject import DirectObject

class BrushManager(DirectObject):

    def __init__(self):
        DirectObject.__init__(self)
        self.brushes = []

    def addBrush(self, brush):
        self.brushes.append(brush)

    def addBrushes(self):
        from .BlockBrush import BlockBrush
        from .ArchBrush import ArchBrush
        from .ConeBrush import ConeBrush
        from .CylinderBrush import CylinderBrush
        from .PipeBrush import PipeBrush
        from .PyramidBrush import PyramidBrush
        from .SphereBrush import SphereBrush
        from .TetrahedronBrush import TetrahedronBrush
        from .TextBrush import TextBrush
        from .TorusBrush import TorusBrush
        from .WedgeBrush import WedgeBrush

        self.addBrush(ArchBrush())
        self.addBrush(BlockBrush())
        self.addBrush(ConeBrush())
        self.addBrush(CylinderBrush())
        self.addBrush(PipeBrush())
        self.addBrush(PyramidBrush())
        self.addBrush(SphereBrush())
        self.addBrush(TetrahedronBrush())
        #self.addBrush(TextBrush())
        #self.addBrush(TorusBrush())
        self.addBrush(WedgeBrush())
