#from panda3d.bsp import BSPMaterial
from panda3d.core import *

from PyQt5 import QtGui, QtCore

# Reference to a material loaded from disk that can be applied to brush faces.
# Materials with the same filename are unified to the same MaterialReference object.
# Stores the $basetexture Texture and the dimensions of it.
class MaterialReference:

    def __init__(self, filename):
        vfs = VirtualFileSystem.getGlobalPtr()
        #self.material = BSPMaterial.getFromFile(filename)
        self.material = MaterialPool.loadMaterial(filename)
        self.filename = filename

        if self.material:
           # baseTexturePath = self.material.getKeyvalue("$basetexture")

            texParam = self.material.getParam("base_color")
            if texParam and isinstance(texParam, MaterialParamTexture):

                tex = texParam.getValue()
                #imageData = bytes(VirtualFileSystem.getGlobalPtr().readFile(baseTexturePath, True))

                pimage = PNMImage()
                tex.store(pimage, 0, 0)
                ss = StringStream()
                pimage.write(ss, "tmp.png")
                imageData = bytes(ss)

                byteArray = QtCore.QByteArray.fromRawData(imageData)
                image = QtGui.QImage.fromData(byteArray)
                self.pixmap = QtGui.QPixmap.fromImage(image)
                self.icon = QtGui.QIcon(self.pixmap)
                self.size = LVector2i(pimage.getXSize(), pimage.getYSize())

                print(pimage, self.size)
            else:
                self.size = LVector2i(64, 64)
                self.icon = None
                self.pixmap = None
        else:
            self.size = LVector2i(64, 64)
            self.icon = None
            self.pixmap = None
