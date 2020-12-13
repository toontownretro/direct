from panda3d.core import BitMask32, CullBinManager, Vec4

#
# Collision masks
#

# Objects
ObjectMask = BitMask32.bit(0)
# Solid faces
FaceMask = BitMask32.bit(1)

# View-specific masks
Mask3D = BitMask32.bit(2)
Mask2D = BitMask32.bit(3)

# Non-object masks
ManipulatorMask = BitMask32.bit(4)

SelectedSort = 1
BoxSort = 2
WidgetSort = 3

PreviewBrush2DColor = Vec4(51 / 255, 223 / 255, 1.0, 1.0)

AppName = "Foundry"

def remapVal(val, A, B, C, D):
    if A == B:
        return D if val >= B else C

    return C + (D - C) * (val - A) / (B - A)

def clamp(val, A, B):
    return max(A, min(B, val))

def colorFromRGBScalar255(color):
    """Takes in a tuple of (r, g, b, scalar) (0-255) and returns a
    linear (0-1) color with the scalar applied."""

    from panda3d.core import VBase4

    scalar = color[3]
    return VBase4(color[0] * (scalar / 255.0) / 255.0,
                  color[1] * (scalar / 255.0) / 255.0,
                  color[2] * (scalar / 255.0) / 255.0,
                  1.0)

def vec3LinearToGamma(vec):
    import math
    vec[0] = math.pow(vec[0], 1.0 / 2.2)
    vec[1] = math.pow(vec[1], 1.0 / 2.2)
    vec[2] = math.pow(vec[2], 1.0 / 2.2)
    return vec

def vec3GammaToLinear(vec):
    import math
    vec[0] = math.pow(vec[0], 2.2)
    vec[1] = math.pow(vec[1], 2.2)
    vec[2] = math.pow(vec[2], 2.2)
    return vec

def reflect(dir, normal):
    return dir - (normal * (dir.dot(normal) * 2.0))

def extrude(start, scale, direction):
    return start + (direction * scale)
