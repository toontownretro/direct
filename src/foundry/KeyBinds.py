from .KeyBindDef import KeyBindDef
from .KeyBind import KeyBind

KeyBinds = [
    KeyBindDef("Create a new map", KeyBind.FileNew, "ctrl+n"),
    KeyBindDef("Open a map", KeyBind.FileOpen, "ctrl+o"),
    KeyBindDef("Save the map", KeyBind.FileSave, "ctrl+s"),
    KeyBindDef("Save the map as", KeyBind.FileSaveAs, "ctrl+shift+s"),
    KeyBindDef("Save all maps", KeyBind.FileSaveAll, "ctrl+alt+s"),
    KeyBindDef("Close the map", KeyBind.FileClose, "ctrl+w"),
    KeyBindDef("Close all maps", KeyBind.FileCloseAll, "ctrl+alt+w"),

    KeyBindDef("Undo previous action", KeyBind.Undo, "ctrl+z"),
    KeyBindDef("Redo previous action", KeyBind.Redo, "ctrl+shift+z"),

    KeyBindDef("Delete object(s)", KeyBind.Delete, "delete"),
    KeyBindDef("Copy object(s)", KeyBind.Copy, "ctrl+c"),
    KeyBindDef("Paste object(s)", KeyBind.Paste, "ctrl+v"),
    KeyBindDef("Select object", KeyBind.Select, "mouse1"),
    KeyBindDef("Select multiple objects", KeyBind.SelectMultiple, "shift"),

    KeyBindDef("Increase grid size", KeyBind.IncGridSize, "]"),
    KeyBindDef("Decrease grid size", KeyBind.DecGridSize, "["),
    KeyBindDef("Toggle 2D grid", KeyBind.Toggle2DGrid, "shift+g"),
    KeyBindDef("Toggle 3D grid", KeyBind.Toggle3DGrid, "shift+h"),
    KeyBindDef("Toggle grid snap", KeyBind.ToggleGridSnap, "shift+j"),

    KeyBindDef("Switch to select tool", KeyBind.SelectTool, "shift+s"),
    KeyBindDef("Switch to move tool", KeyBind.MoveTool, "shift+m"),
    KeyBindDef("Switch to rotate tool", KeyBind.RotateTool, "shift+r"),
    KeyBindDef("Switch to scale tool", KeyBind.ScaleTool, "shift+q"),
    KeyBindDef("Switch to entity tool", KeyBind.EntityTool, "shift+e"),
    KeyBindDef("Switch to block tool", KeyBind.BlockTool, "shift+b"),
    KeyBindDef("Switch to clipping tool", KeyBind.ClipTool, "shift+x"),

    KeyBindDef("Select mode - groups", KeyBind.SelectGroups, "ctrl+shift+g"),
    KeyBindDef("Select mode - faces", KeyBind.SelectFaces, "ctrl+shift+f"),
    KeyBindDef("Select mode - objects", KeyBind.SelectObjects, "ctrl+shift+o"),
    KeyBindDef("Select mode - vertices", KeyBind.SelectVertices, "ctrl+shift+v"),

    KeyBindDef("Confirm action", KeyBind.Confirm, "enter"),
    KeyBindDef("Cancel action", KeyBind.Cancel, "escape"),

    KeyBindDef("Toggle 3D mouse look", KeyBind.FlyCam, "z"),

    KeyBindDef("2D view - pan camera", KeyBind.Pan2DView, "mouse2"),
    KeyBindDef("Zoom in", KeyBind.ZoomIn, "wheel_up"),
    KeyBindDef("Zoom out", KeyBind.ZoomOut, "wheel_down"),

    KeyBindDef("3D view - move forward", KeyBind.Forward3DView, "w"),
    KeyBindDef("3D view - move back", KeyBind.Back3DView, "s"),
    KeyBindDef("3D view - move left", KeyBind.Left3DView, "a"),
    KeyBindDef("3D view - move right", KeyBind.Right3DView, "d"),
    KeyBindDef("3D view - move up", KeyBind.Up3DView, "q"),
    KeyBindDef("3D view - move down", KeyBind.Down3DView, "e"),
    KeyBindDef("3D view - look up", KeyBind.LookUp3DView, "arrow_up"),
    KeyBindDef("3D view - look down", KeyBind.LookDown3DView, "arrow_down"),
    KeyBindDef("3D view - look left", KeyBind.LookLeft3DView, "arrow_left"),
    KeyBindDef("3D view - look right", KeyBind.LookRight3DView, "arrow_right"),

    KeyBindDef("Switch to next document", KeyBind.NextDocument, "tab"),
    KeyBindDef("Switch to previous document", KeyBind.PrevDocument, "shift+tab"),

    KeyBindDef("Exit the application", KeyBind.Exit, "alt+f4"),

    KeyBindDef("Arrange viewports in quad splitter", KeyBind.ViewQuads, "f1"),
    KeyBindDef("Focus 3D view", KeyBind.View3D, "f2"),
    KeyBindDef("Focus XY view", KeyBind.ViewXY, "f3"),
    KeyBindDef("Focus YZ view", KeyBind.ViewYZ, "f4"),
    KeyBindDef("Focus XZ view", KeyBind.ViewXZ, "f5"),

    KeyBindDef("Switch to DNA tool", KeyBind.DNATool, "shift+d"),

    KeyBindDef("Group selected objects", KeyBind.GroupSelected, "ctrl+g"),
    KeyBindDef("Ungroup selected objects", KeyBind.UngroupSelected, "ctrl+shift+g"),

    KeyBindDef("Cut selected objects", KeyBind.Cut, "ctrl+x"),

    KeyBindDef("Tie to world", KeyBind.TieToWorld, "ctrl+shift+w"),
    KeyBindDef("Tie to entity", KeyBind.TieToEntity, "ctrl+t"),

    KeyBindDef("Run map", KeyBind.Run, "f9")
]

KeyBindsByID = {x.id: x for x in KeyBinds}

def getShortcut(id):
    return KeyBindsByID[id].shortcut

def getPandaShortcut(id):
    return KeyBindsByID[id].asPandaShortcut()

def getQtShortcut(id):
    return KeyBindsByID[id].asQtShortcut()
