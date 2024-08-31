from panda3d.core import Vec4

class GridSettings:
    DefaultStep = 1
    Highlight1Toggle = True
    Highlight1Line = 8
    Highlight1 = Vec4(128 / 255.0, 128 / 255.0, 128 / 255.0, 1.0)
    Highlight2Toggle = True
    Highlight2Unit = 64
    Highlight2 = Vec4(100 / 255.0, 46 / 255.0, 0, 1.0)
    GridSnap = True
    EnableGrid = True
    EnableGrid3D = True
    GridLines = Vec4(75 / 255.0, 75 / 255.0, 75 / 255.0, 1.0)
    #ZeroLines = Vec4(0 / 255.0, 100 / 255.0, 100 / 255.0, 1.0)
    BoundaryLines = Vec4(1, 0, 0, 1)
    HideSmallerToggle = True
    HideSmallerThan = 4
    HideFactor = 8
    Low = -1024
    High = 1024
