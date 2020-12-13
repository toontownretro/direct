from enum import IntEnum

class KeyBind(IntEnum):

    FileNew = 0
    FileSave = 1
    FileSaveAs = 2
    FileOpen = 3
    FileClose = 4

    Undo = 5
    Redo = 6

    Delete = 9
    Copy = 10
    Paste = 11

    IncGridSize = 12
    DecGridSize = 13
    Toggle2DGrid = 14
    Toggle3DGrid = 15
    ToggleGridSnap = 16

    SelectTool = 17
    MoveTool = 18
    RotateTool = 19
    ScaleTool = 20
    EntityTool = 21
    BlockTool = 22
    ClipTool = 23

    SelectGroups = 24
    SelectObjects = 25
    SelectFaces = 26
    SelectVertices = 27

    Confirm = 28
    Cancel = 29

    Pan2DView = 31
    ZoomOut = 32
    ZoomIn = 33

    FlyCam = 34
    Forward3DView = 35
    Left3DView = 36
    Right3DView = 37
    Back3DView = 38
    Up3DView = 39
    Down3DView = 40
    LookLeft3DView = 41
    LookRight3DView = 42
    LookUp3DView = 43
    LookDown3DView = 44

    Select = 45
    SelectMultiple = 46

    NextDocument = 47
    PrevDocument = 48

    Exit = 49

    FileSaveAll = 50
    FileCloseAll = 51

    ViewQuads = 52
    View3D = 53
    ViewXY = 54
    ViewYZ = 55
    ViewXZ = 56

    DNATool = 57

    GroupSelected = 58
    UngroupSelected = 59

    Cut = 60

    TieToWorld = 61
    TieToEntity = 62

    Run = 63
