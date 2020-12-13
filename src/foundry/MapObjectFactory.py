from .World import World
from .Entity import Entity
from .Solid import Solid
from .Group import Group

# object name in pmap file to object class
MapObjectsByName = {
    "world": World,
    "entity": Entity,
    "solid": Solid,
    "group": Group
}
