from .BaseEditor import BaseEditor
from .ScrubSpinBox import DoubleScrubSpinBox, MinVal, MaxVal

from PyQt5 import QtCore

class BaseVecEditor(BaseEditor):

    class ComponentSpinBox(DoubleScrubSpinBox):

        def __init__(self, editor, component):
            DoubleScrubSpinBox.__init__(self, editor)
            self.component = component
            self.editor = editor
            self.setRange(MinVal, MaxVal)
            self.valueChanged.connect(self.__valueChanged)
            self.setKeyboardTracking(False)
            self.setAccelerated(True)
            self.editor.layout().addWidget(self)

        def __valueChanged(self, val):
            self.editor.componentChanged()

    def __init__(self, parent, item, model, numComponents):
        BaseEditor.__init__(self, parent, item, model)
        self.components = []
        for i in range(numComponents):
            spinBox = BaseVecEditor.ComponentSpinBox(self, i)
            self.components.append(spinBox)

    def componentChanged(self):
        self.setModelData(self.model, self.item.index())

    def setEditorData(self, index):
        data = self.getItemData()
        comps = data.split(' ')
        for i in range(len(self.components)):
            self.components[i].blockSignals(True)
            self.components[i].setValue(float(comps[i]))
            self.components[i].blockSignals(False)

    def setModelData(self, model, index):
        data = ""
        for i in range(len(self.components)):
            strVal = str(self.components[i].value())
            if i < len(self.components) - 1:
                data += "%s " % strVal
            else:
                data += strVal
        model.setData(index, data, QtCore.Qt.EditRole)

class Vec2Editor(BaseVecEditor):

    def __init__(self, parent, item, model):
        BaseVecEditor.__init__(self, parent, item, model, 2)

class Vec3Editor(BaseVecEditor):

    def __init__(self, parent, item, model):
        BaseVecEditor.__init__(self, parent, item, model, 3)

class Vec4Editor(BaseVecEditor):

    def __init__(self, parent, item, model):
        BaseVecEditor.__init__(self, parent, item, model, 4)
