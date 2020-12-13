from .ColorEditor import ColorEditor
from .IntegerEditor import IntegerEditor
from .ChoicesEditor import ChoicesEditor
from .StringEditor import StringEditor
from .StudioEditor import StudioEditor
from .VecEditor import Vec2Editor, Vec3Editor, Vec4Editor
from .FloatEditor import FloatEditor
from .BooleanEditor import BooleanEditor

from PyQt5 import QtWidgets

class ObjectPropertiesDelegate(QtWidgets.QStyledItemDelegate):

    PropTypeEditors = {
        "color255": ColorEditor,
        "integer": IntegerEditor,
        "choices": ChoicesEditor,
        "string": StringEditor,
        "studio": StudioEditor,
        "target_source": StringEditor,
        "target_destination": StringEditor,
        "vec3": Vec3Editor,
        "vec2": Vec2Editor,
        "vec4": Vec4Editor,
        "float": FloatEditor,
        "boolean": BooleanEditor
    }

    def __init__(self, window):
        QtWidgets.QStyledItemDelegate.__init__(self)
        self.window = window

    def getItem(self, idx):
        return self.window.propertiesModel.itemFromIndex(idx)

    def setEditorData(self, editor, index):
        item = self.getItem(index)
        editorCls = self.PropTypeEditors.get(item.propType, None)
        if editorCls:
            editor.setEditorData(index)
            return
        QtWidgets.QStyledItemDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor, model, index):
        item = self.getItem(index)
        editorCls = self.PropTypeEditors.get(item.propType, None)
        if editorCls:
            editor.setModelData(model, index)
            return
        QtWidgets.QStyledItemDelegate.setModelData(self, editor, model, index)

    def createEditor(self, parent, option, index):
        item = self.getItem(index)
        editor = self.PropTypeEditors.get(item.propType, None)
        if editor:
            return editor(parent, item, self.window.propertiesModel)
        else:
            return QtWidgets.QStyledItemDelegate.createEditor(self, parent, option, index)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
