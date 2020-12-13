from panda3d.core import Filename

from .MaterialReference import MaterialReference

MaterialRefs = {}

def getMaterial(filename):
    global MaterialRefs
    filename = Filename(filename)
    fullpath = filename.getFullpath()
    #if not fullpath.endswith(".mat"):
    #    fullpath += ".mat"
    #    fullpath = fullpath.lower()
    if fullpath in MaterialRefs:
        ref = MaterialRefs[fullpath]
    else:
        ref = MaterialReference(Filename(fullpath))
        MaterialRefs[fullpath] = ref
    return ref

ActiveMaterial = None

def setActiveMaterial(mat):
    global ActiveMaterial
    ActiveMaterial = mat
    messenger.send('activeMaterialChanged', [mat])
