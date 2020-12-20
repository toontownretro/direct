from .ModelHelper import ModelHelper
from .SpriteHelper import SpriteHelper
from .LightHelper import LightHelper
from .SpotlightHelper import SpotlightHelper
from .AmbientLightHelper import AmbientLightHelper
from .DirLightHelper import DirLightHelper

# Map helpers by entity class definitions in the fgd file.
Helpers = {
    "studio": ModelHelper,
    "studioprop": ModelHelper,
    "lightprop": ModelHelper,
    "iconsprite": SpriteHelper,
    "pointlight": LightHelper,
    "spotlight": SpotlightHelper,
    "ambientlight": AmbientLightHelper,
    "dirlight": DirLightHelper
}

def createHelper(helperInfo, mapObject):
    helperCls = Helpers.get(helperInfo['name'])
    if helperCls:
        helper = helperCls(mapObject)
        helper.generate(helperInfo)
        return helper
    return None
