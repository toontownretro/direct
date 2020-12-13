import sys

try:
    import PyQt5
except ImportError:
    print("ERROR: You need to pull in PyQt5 via pip to use the level editor")
    sys.exit(1)

try:
    import py_linq
except ImportError:
    print("ERROR: You need to pull in py_linq via pip to use the level editor")
    sys.exit(1)

from PyQt5 import QtWidgets, QtGui

import builtins

from panda3d.core import loadPrcFile, loadPrcFileData, ConfigVariableString, ConfigVariableDouble
loadPrcFileData('', 'window-type none')

from direct.foundry.LevelEditor import LevelEditor
base = LevelEditor()

ConfigVariableDouble('decompressor-step-time').setValue(0.01)
ConfigVariableDouble('extractor-step-time').setValue(0.01)

print("taha")

base.run()
