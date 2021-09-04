from panda3d.core import Point3, Vec3, Quat, LineSegs, KeyValues, ButtonRegistry
from panda3d.core import LPlane, Vec4, Filename, VirtualFileSystem, getModelPath

from direct.showbase.PythonUtil import invertDict

from direct.foundry import LEGlobals

from PyQt5 import QtGui, QtCore

import math, random

# Qt key codes -> Panda KeyboardButton names.
QtKeyToKeyboardButton = {
    QtCore.Qt.Key_Space: "space",
    QtCore.Qt.Key_Backspace: "backspace",
    QtCore.Qt.Key_Tab: "tab",
    QtCore.Qt.Key_Return: "enter",
    QtCore.Qt.Key_Escape: "escape",
    QtCore.Qt.Key_Delete: "delete",

    QtCore.Qt.Key_F1: "f1",
    QtCore.Qt.Key_F2: "f2",
    QtCore.Qt.Key_F3: "f3",
    QtCore.Qt.Key_F4: "f4",
    QtCore.Qt.Key_F5: "f5",
    QtCore.Qt.Key_F6: "f6",
    QtCore.Qt.Key_F7: "f7",
    QtCore.Qt.Key_F8: "f8",
    QtCore.Qt.Key_F9: "f9",
    QtCore.Qt.Key_F10: "f10",
    QtCore.Qt.Key_F11: "f11",
    QtCore.Qt.Key_F12: "f12",
    QtCore.Qt.Key_F13: "f13",
    QtCore.Qt.Key_F14: "f14",
    QtCore.Qt.Key_F15: "f15",
    QtCore.Qt.Key_F16: "f16",

    QtCore.Qt.Key_Left: "arrow_left",
    QtCore.Qt.Key_Right: "arrow_right",
    QtCore.Qt.Key_Up: "arrow_up",
    QtCore.Qt.Key_Down: "arrow_down",
    QtCore.Qt.Key_PageDown: "page_down",
    QtCore.Qt.Key_PageUp: "page_up",
    QtCore.Qt.Key_Home: "home",
    QtCore.Qt.Key_End: "end",
    QtCore.Qt.Key_Insert: "insert",
    QtCore.Qt.Key_Help: "help",

    QtCore.Qt.Key_Shift: "shift",
    QtCore.Qt.Key_Control: "control",
    QtCore.Qt.Key_Alt: "alt",
    QtCore.Qt.Key_Meta: "meta",
    QtCore.Qt.Key_CapsLock: "caps_lock",
    QtCore.Qt.Key_NumLock: "num_lock",
    QtCore.Qt.Key_ScrollLock: "scroll_lock",
    QtCore.Qt.Key_Pause: "pause",
    QtCore.Qt.Key_Menu: "menu",
}

KeyboardButtonToQtKey = invertDict(QtKeyToKeyboardButton)

def keyboardButtonFromQtKey(keycode):
    reg = ButtonRegistry.ptr()

    # First try the ascii value
    asciiValue = keycode
    if asciiValue < 256:
        button = reg.findAsciiButton(chr(asciiValue).lower())
    else:
        # Don't have a valid ascii value for this key.
        # Look up the KeyboardButton name by the key code.
        buttonName = QtKeyToKeyboardButton.get(asciiValue)
        button = reg.findButton(buttonName)
    return button

def qtKeyFromKeyboardButton(name):
    if len(name) == 1:
        # A single character.. this must be an ascii key
        return ord(name)
    else:
        return KeyboardButtonToQtKey.get(name)

def strToQColor(colorStr, alpha = False):
    pcolor = KeyValues.to4f(colorStr)
    return QtGui.QColor(int(pcolor.x), int(pcolor.y), int(pcolor.z), 255 if not alpha else int(pcolor.w))

def qColorToStr(qcolor):
    return "%i %i %i %i" % (qcolor.red(), qcolor.green(), qcolor.blue(), qcolor.alpha())

def snapToGrid(gridSize, point):
    result = Point3(point)
    for i in range(3):
        increments = int(round(result[i] / gridSize))
        result[i] = increments * gridSize

    return result

def makeForwardAxis(vec, quat):
    invQuat = Quat()
    invQuat.invertFrom(quat)
    result = invQuat.xform(vec)
    result.setY(0.0)
    return result

def zeroParallelAxis(vec, quat):
    axis = Vec3(1, 0, 1)
    axis = quat.xform(axis)

    return Vec3(vec[0] * axis[0],
                vec[1] * axis[1],
                vec[2] * axis[2])

def makeCubeOutline(mins, maxs, color, thickness = 1.0):
    lines = LineSegs()
    lines.setColor(color)
    lines.setThickness(thickness)
    lines.move_to( mins )
    lines.draw_to( Point3( mins.get_x(), mins.get_y(), maxs.get_z() ) )
    lines.draw_to( Point3( mins.get_x(), maxs.get_y(), maxs.get_z() ) )
    lines.draw_to( Point3( mins.get_x(), maxs.get_y(), mins.get_z() ) )
    lines.draw_to( mins )
    lines.draw_to( Point3( maxs.get_x(), mins.get_y(), mins.get_z() ) )
    lines.draw_to( Point3( maxs.get_x(), mins.get_y(), maxs.get_z() ) )
    lines.draw_to( Point3( mins.get_x(), mins.get_y(), maxs.get_z() ) )
    lines.move_to( Point3( maxs.get_x(), mins.get_y(), maxs.get_z() ) )
    lines.draw_to( maxs )
    lines.draw_to( Point3( mins.get_x(), maxs.get_y(), maxs.get_z() ) )
    lines.move_to( maxs )
    lines.draw_to( Point3( maxs.get_x(), maxs.get_y(), mins.get_z() ) )
    lines.draw_to( Point3( mins.get_x(), maxs.get_y(), mins.get_z() ) )
    lines.move_to( Point3( maxs.get_x(), maxs.get_y(), mins.get_z() ) )
    lines.draw_to( Point3( maxs.get_x(), mins.get_y(), mins.get_z() ) )
    return lines.create()

def hasNetEffect(np, effect):
    if np.hasEffect(effect):
        return True

    if np.hasParent():
        return hasNetEffect(np.getParent(), effect)

    return False

def hasNetBillboard(np):
    # Returns true if this node or any ancestor of this node contains a BillboardEffect.
    from panda3d.core import BillboardEffect
    return hasNetEffect(np, BillboardEffect.getClassType())

def closestDistanceBetweenLines(l1, l2):
    org1 = l1.getOrigin()
    org2 = l2.getOrigin()
    dir1 = l1.getDirection()
    dir2 = l2.getDirection()

    dp = org2 - org1
    v12 = dir1.dot(dir1)
    v22 = dir2.dot(dir2)
    v1v2 = dir1.dot(dir2)

    det = v1v2 * v1v2 - v12 * v22

    if abs(det) > 0.0:
        invDet = 1.0 / det
        dpv1 = dp.dot(dir1)
        dpv2 = dp.dot(dir2)

        l1.t = invDet * (v22 * dpv1 - v1v2 * dpv2)
        l2.t = invDet * (v1v2 * dpv1 - v12 * dpv2)

        return (dp + dir2 * l2.t - dir1 * l1.t)

    else:
        a = dp.cross(dir1)
        return math.sqrt(a.dot(a) / v12)

def roundVector(vec, num = 8):
    for i in range(len(vec)):
        vec[i] = round(vec[i], num)
    return vec

def strToBool(string):
    return bool(int(string))

def boolToStr(boolean):
    return str(int(boolean))

# THE FACES ARE COUNTER-CLOCKWISE!!!
def getBoxFaces(start, end, roundDecimals = 8):
    topLeftBack = roundVector(Point3(start.x, end.y, end.z), roundDecimals)
    topRightBack = roundVector(end, roundDecimals)
    topLeftFront = roundVector(Point3(start.x, start.y, end.z), roundDecimals)
    topRightFront = roundVector(Point3(end.x, start.y, end.z), roundDecimals)

    bottomLeftBack = roundVector(Point3(start.x, end.y, start.z), roundDecimals)
    bottomRightBack = roundVector(Point3(end.x, end.y, start.z), roundDecimals)
    bottomLeftFront = roundVector(start, roundDecimals)
    bottomRightFront = roundVector(Point3(end.x, start.y, start.z), roundDecimals)

    return [
        [topLeftFront, topRightFront, bottomRightFront, bottomLeftFront],
        [topRightBack, topLeftBack, bottomLeftBack, bottomRightBack],
        [topLeftBack, topLeftFront, bottomLeftFront, bottomLeftBack],
        [topRightFront, topRightBack, bottomRightBack, bottomRightFront],
        [topLeftBack, topRightBack, topRightFront, topLeftFront],
        [bottomLeftFront, bottomRightFront, bottomRightBack, bottomLeftBack]
    ]

def getBoxPlanes(start, end):
    faces = getBoxFaces(start, end)
    planes = []
    for i in range(6):
        planes.append(LPlane(faces[i][0], faces[i][1], faces[i][2]))
    return planes

def getClosestAxis(normal):
    absNormal = Vec3(abs(normal.x), abs(normal.y), abs(normal.z))
    if absNormal.almostEqual(Vec3.unitX(), 0.5):
        return Vec3.unitX()
    elif absNormal.almostEqual(Vec3.unitY(), 0.5):
        return Vec3.unitY()
    else:
        return Vec3.unitZ()

def circle(x, y, radius, vertices=32):
    # Doesn't actually define a "circle" -- more of a pentagon. :)
    result = []
    for theta in range(0, 360, 360//vertices):
        theta *= math.pi/180 # Degrees to radians
        result.append((x + math.sin(theta)*radius, y + math.cos(theta)*radius))
    return result

def getRandomSolidColor():
    # Picks a random shade of blue/green.
    return Vec4(0, random.uniform(0.6, 1.0), random.uniform(0.6, 1.0), 1.0)

def qtResolvePath(filename):
    """
    Resolves a filename path using the Panda model-path and returns an
    OS-specific absolute path.  Used to load Qt icons from stuff on model-path.
    """
    filename = Filename.fromOsSpecific(filename)
    vfs = VirtualFileSystem.getGlobalPtr()
    vfs.resolveFilename(filename, getModelPath().getValue())
    return filename.toOsSpecific()

