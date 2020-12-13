# Filename: MetaData.py
# Author:  Brian Lach (July 10, 2020)
# Purpose: Provides info about entity metadata types and how to serialize/unserialize them.

from panda3d.core import LVecBase3f, LVecBase2f, LVecBase4f, CKeyValues

from direct.fgd import FgdEntityProperty
from direct.foundry import LEUtils

MetaDataExclusions = [
    'id',
    'classname',
    'visgroup'
]

# (type, unserialize func, serialize func, default value)
MetaDataType = {
    'string': (str, str, str, ""),
    'decal': (str, str, str, ""),
    'sound': (str, str, str, ""),
    'float': (float, float, str, 0.0),
    'color255': (LVecBase4f, CKeyValues.to4f, CKeyValues.toString, LVecBase4f(255, 255, 255, 255)),
    'vec3': (LVecBase3f, CKeyValues.to3f, CKeyValues.toString, LVecBase3f(0, 0, 0)),
    'vec4': (LVecBase4f, CKeyValues.to4f, CKeyValues.toString, LVecBase4f(0, 0, 0, 0)),
    'vec2': (LVecBase2f, CKeyValues.to2f, CKeyValues.toString, LVecBase2f(0, 0)),
    'integer': (int, int, str, 0),
    'choices': (int, int, str, 0),
    'flags': (int, int, str, 0),
    'studio': (str, str, str, ""),
    'target_source': (str, str, str, ""),
    'target_destination': (str, str, str, ""),
    'target_destinations': (str, str, str, ""),
    'boolean': (bool, LEUtils.strToBool, LEUtils.boolToStr, False)
}

def getMetaDataType(valueType):
    return MetaDataType[valueType]

def getNativeType(typeName):
    return MetaDataType[typeName][0]

def getUnserializeFunc(typeName):
    return MetaDataType[typeName][1]

def getSerializeFunc(typeName):
    return MetaDataType[typeName][2]

def getDefaultValue(typeName):
    return MetaDataType[typeName][3]

def isPropertyExcluded(propName):
    return propName in MetaDataExclusions
