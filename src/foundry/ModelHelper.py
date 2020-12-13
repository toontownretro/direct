from panda3d.core import ModelNode, NodePath, Vec4, CKeyValues, Vec3
#from panda3d.bsp import BSPMaterialAttrib

from .MapHelper import MapHelper

class ModelHelper(MapHelper):

    ChangeWith = [
        "model"
    ]

    def __init__(self, mapObject):
        MapHelper.__init__(self, mapObject)
        self.modelRoot = NodePath(ModelNode("modelHelper"))
        self.modelRoot.setScale(16.0)
        self.modelRoot.reparentTo(self.mapObject.helperRoot)

        self.vpRoots = []

    def setSelectedState(self):
        for vp, vpRoot in self.vpRoots:
            if vp.is2D():
                # Show unlit, untextured, blue wireframe in 2D
                vpRoot.setRenderModeFilled()
                vpRoot.setLightOff(1)
                vpRoot.setFogOff(1)
                vpRoot.clearTexture()
                #vpRoot.clearAttrib(BSPMaterialAttrib)
                vpRoot.setTransparency(1)
                vpRoot.setColor(Vec4(1, 1, 1, 0.75), 1)
            else:
                vpRoot.setColorScale(Vec4(1, 1, 1, 1))

    def setUnselectedState(self):
        for vp, vpRoot in self.vpRoots:
            if vp.is2D():
                # Show unlit, untextured, blue wireframe in 2D
                vpRoot.setRenderModeWireframe()
                vpRoot.setLightOff(1)
                vpRoot.setFogOff(1)
                vpRoot.setTextureOff(1)
                #vpRoot.setBSPMaterial("phase_14/materials/unlit.mat", 1)
                vpRoot.setColor(Vec4(0.016, 1, 1, 1), 1)
                vpRoot.clearTransparency()
            else:
                vpRoot.setColorScale(Vec4(1, 1, 1, 1))

    def select(self):
        self.setSelectedState()

    def deselect(self):
        self.setUnselectedState()

    def generate(self, helperInfo):
        MapHelper.generate(self)

        args = helperInfo['args']
        modelPath = args[0] if len(args) > 0 else None
        if not modelPath:
            # Model wasn't specified in the class definition,
            # check for a property called "model"
            modelPath = self.mapObject.getPropertyValue("model", default = "models/smiley.egg.pz")
        else:
            # For some reason the fgd parser doesn't remove the quotes around the
            # model path string in the game class definition
            modelPath = modelPath.replace("\"", "")
        if not modelPath:
            return

        modelNp = base.loader.loadModel(modelPath, okMissing = True)
        if not modelNp:
            return

        # Create a representation in each viewport
        for vp in base.viewportMgr.viewports:
            vpRoot = self.modelRoot.attachNewNode("vpRepr")
            vpRoot.hide(~vp.getViewportMask())
            self.vpRoots.append((vp, vpRoot))

            vpModel = modelNp.instanceTo(vpRoot)

        if self.mapObject.selected:
            self.setSelectedState()
        else:
            self.setUnselectedState()

    def cleanup(self):
        self.vpRoots = []
        if self.modelRoot:
            self.modelRoot.removeNode()
            self.modelRoot = None
        MapHelper.cleanup(self)
