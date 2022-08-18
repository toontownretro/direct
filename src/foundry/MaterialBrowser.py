from .AssetBrowser import AssetBrowser
from direct.foundry import MaterialPool

from PyQt5 import QtCore, QtGui

class MaterialBrowser(AssetBrowser):

    FileExtensions = ["mto", "pmat"]

    Thumbnails = {}

    def getThumbnail(self, filename, context):
        # Delay the thumbnail loading so we don't freeze the application loading
        # a ton of materials at once, and so we don't get a stack overflow calling
        # this method a bunch of times.

        if filename in self.Thumbnails:
            icon = self.Thumbnails[filename]
        else:
            ref = MaterialPool.getMaterial(filename)
            if ref.pixmap:
                pixmap = ref.pixmap.scaled(96, 96, QtCore.Qt.KeepAspectRatio,
                                          QtCore.Qt.SmoothTransformation)
                icon = QtGui.QIcon(pixmap)
            else:
                icon = QtGui.QIcon("Not Found")

            self.Thumbnails[filename] = icon

        return icon
