from panda3d.core import GeomVertexData, GeomEnums, NodePath, GeomVertexArrayFormat
from panda3d.core import GeomNode, GeomTriangles, GeomLinestrips, GeomVertexFormat
from panda3d.core import GeomVertexWriter, InternalName, Vec4, Geom
from panda3d.core import ColorAttrib, Vec3, Vec2, deg2Rad, Quat, Point3
from panda3d.core import CullFaceAttrib, AntialiasAttrib, KeyValues, LVector2i
from panda3d.core import RenderState, TransparencyAttrib, ColorScaleAttrib, DepthTestAttrib, DepthWriteAttrib, CullBinAttrib
from panda3d.core import TextureAttrib
#from panda3d.bsp import PlaneCulledGeomNode, BSPMaterialAttrib
#from panda3d.editor import SolidFaceGeom
from panda3d.direct import SolidFaceGeom, PlaneCulledGeomNode

from .MapWritable import MapWritable
from .SolidVertex import SolidVertex

from direct.foundry.ViewportType import VIEWPORT_3D_MASK, VIEWPORT_2D_MASK, VIEWPORT_3D_FULL
from direct.foundry import LEUtils, LEGlobals, LEConfig
from direct.foundry import PlaneClassification
from direct.foundry.Plane import Plane
from direct.foundry.Align import Align
from direct.foundry.IDGenerator import IDGenerator
from direct.foundry import MaterialPool

from enum import IntEnum

FaceFormat = None
def getFaceFormat():
    global FaceFormat
    if not FaceFormat:
        arr = GeomVertexArrayFormat()
        arr.addColumn(InternalName.getVertex(), 3, GeomEnums.NTStdfloat, GeomEnums.CPoint)
        arr.addColumn(InternalName.getNormal(), 3, GeomEnums.NTStdfloat, GeomEnums.CNormal)
        arr.addColumn(InternalName.getTangent(), 3, GeomEnums.NTStdfloat, GeomEnums.CVector)
        arr.addColumn(InternalName.getBinormal(), 3, GeomEnums.NTStdfloat, GeomEnums.CVector)
        arr.addColumn(InternalName.getTexcoord(), 2, GeomEnums.NTStdfloat, GeomEnums.CTexcoord)
        FaceFormat = GeomVertexFormat.registerFormat(arr)
    return FaceFormat

class FaceOrientation(IntEnum):
    Floor = 0
    Ceiling = 1
    NorthWall = 2
    SouthWall = 3
    EastWall = 4
    WestWall = 5
    Invalid = 6

FaceNormals = [
    Vec3(0, 0, 1),  # floor
    Vec3(0, 0, -1), # ceiling
    Vec3(0, -1, 0), # north wall
    Vec3(0, 1, 0),  # south wall
    Vec3(-1, 0, 0), # east wall
    Vec3(1, 0, 0)   # west wall
]

DownVectors = [
    Vec3(0, -1, 0), # floor
    Vec3(0, -1, 0), # ceiling
    Vec3(0, 0, -1), # north wall
    Vec3(0, 0, -1), # south wall
    Vec3(0, 0, -1), # east wall
    Vec3(0, 0, -1)  # west wall
]

RightVectors = [
    Vec3(1, 0, 0),  # floor
    Vec3(1, 0, 0),  # ceiling
    Vec3(1, 0, 0),  # north wall
    Vec3(1, 0, 0),  # south wall
    Vec3(0, 1, 0),  # east wall
    Vec3(0, 1, 0)   # west wall
]

PreviewAlpha = 0.75

class FaceMaterial:

    def __init__(self):
        self.material = None
        self.tangent = Vec3(1, 0, 0)
        self.binormal = Vec3(0, 0, 1)
        self.scale = Vec2(LEConfig.default_texture_scale.getValue())
        self.shift = LVector2i(0, 0)
        self.uAxis = Vec3(0)
        self.vAxis = Vec3(0)
        self.rotation = 0.0
        self.lightmapScale = LEConfig.default_lightmap_scale.getValue()

    def cleanup(self):
        self.material = None
        self.scale = None
        self.shift = None
        self.uAxis = None
        self.vAxis = None
        self.rotation = None
        self.lightmapScale = None

    def setVAxisFromOrientation(self, face):
        self.uAxis = Vec3(0)
        self.vAxis = Vec3(0)

        # Determine the general orientation of this face (floor, ceiling, n wall, etc.)
        orientation = face.getOrientation()
        if orientation == FaceOrientation.Invalid:
            return orientation

        # Pick a world axis aligned V axis based on the face orientation.
        self.vAxis = DownVectors[orientation]

        return orientation

    def alignTextureToFace(self, face):
        # Set the U and V axes to match the plane's normal
        # Need to start with the world alignment on the V axis so that we don't align backwards.
        # Then we can calculate U based on that, and the real V afterwards.

        orientation = self.setVAxisFromOrientation(face)
        if orientation == FaceOrientation.Invalid:
            return

        plane = face.getWorldPlane()
        normal = plane.getNormal()

        #
        # Calculate the texture axes.
        #

        # Using the axis-aligned V axis, calculate the true U axis
        self.uAxis = normal.cross(self.vAxis).normalized()

        # Now use the true U axis to calculate the true V axis.
        self.vAxis = self.uAxis.cross(normal).normalized()

        self.rotation = 0.0

    def alignTextureToWorld(self, face):
        # Set the U and V axes to match the X, Y, or Z axes.
        # How they are calculated depends on which direction the plane is facing.

        orientation = self.setVAxisFromOrientation(face)
        if orientation == FaceOrientation.Invalid:
            return

        self.uAxis = RightVectors[orientation]
        self.rotation = 0

    def setTextureRotation(self, angle):
        # Rotate texture around the face normal
        rads = deg2Rad(self.rotation - angle)
        # Rotate around the face normal
        texNorm = self.vAxis.cross(self.uAxis).normalized()
        transform = Quat()
        transform.setFromAxisAngleRad(rads, texNorm)
        self.uAxis = transform.xform(self.uAxis)
        self.vAxis = transform.xform(self.vAxis)
        self.rotation = angle

    def fitTextureToPointCloud(self, cloud, tileX, tileY):
        if self.material is None:
            return
        if tileX <= 0:
            tileX = 1
        if tileY <= 0:
            tileY = 1

        # Scale will change, no need to use it in the calculations
        xvals = []
        yvals = []
        for extent in cloud.extents:
            xvals.append(extent.dot(self.uAxis))
            yvals.append(extent.dot(self.vAxis))

        minU = min(xvals)
        minV = min(yvals)
        maxU = max(xvals)
        maxV = max(yvals)

        self.scale.x = (maxU - minU) / (self.material.size.x * tileX)
        self.scale.y = (maxV - minV) / (self.material.size.y * tileY)
        self.shift.x = -minU / self.scale.x
        self.shift.y = -minV / self.scale.y

    def alignTextureWithPointCloud(self, cloud, mode):
        if self.material is None:
            return

        xvals = []
        yvals = []
        for extent in cloud.extents:
            xvals.append(extent.dot(self.uAxis) / self.scale.x)
            yvals.append(extent.dot(self.vAxis) / self.scale.y)

        minU = min(xvals)
        minV = min(yvals)
        maxU = max(xvals)
        maxV = max(yvals)

        if mode == Align.Left:
            self.shift.x = -minU
        elif mode == Align.Right:
            self.shift.x = -maxU + self.material.size.x
        elif mode == Align.Center:
            avgU = (minU + maxU) / 2
            avgV = (minV + maxV) / 2
            self.shift.x = -avgU + self.material.size.x / 2
            self.shift.y = -avgV + self.material.size.y / 2
        elif mode == Align.Top:
            self.shift.y = -minV
        elif mode == Align.Bottom:
            self.shift.y = -maxV + self.material.size.y

    def writeKeyValues(self, kv):
        kv.setKeyValue("material", self.material.filename.getFullpath())
        kv.setKeyValue("uaxis", "[%f %f %f %i] %f" % (self.uAxis[0], self.uAxis[1], self.uAxis[2],
                                                      self.shift[0], self.scale[0]))
        kv.setKeyValue("vaxis", "[%f %f %f %i] %f" % (self.vAxis[0], self.vAxis[1], self.vAxis[2],
                                                      self.shift[1], self.scale[1]))
        kv.setKeyValue("rotation", str(self.rotation))
        kv.setKeyValue("lightmap_scale", str(self.lightmapScale))

    def readKeyValues(self, kv):
        self.material = MaterialPool.getMaterial(kv.getValue("material"))

        shiftScale = Vec2()
        kv.parseMaterialAxis(kv.getValue("uaxis"), self.uAxis, shiftScale)
        self.shift[0] = int(shiftScale[0])
        self.scale[0] = shiftScale[1]
        kv.parseMaterialAxis(kv.getValue("vaxis"), self.vAxis, shiftScale)
        self.shift[1] = int(shiftScale[0])
        self.scale[1] = shiftScale[1]

        self.rotation = float(kv.getValue("rotation"))
        if kv.hasKey("lightmap_scale"):
            self.lightmapScale = int(kv.getValue("lightmap_scale"))

    def clone(self):
        mat = FaceMaterial()
        mat.material = self.material
        mat.scale = Vec2(self.scale)
        mat.shift = LVector2i(self.shift)
        mat.uAxis = Vec3(self.uAxis)
        mat.vAxis = Vec3(self.vAxis)
        mat.rotation = float(self.rotation)
        return mat

class SolidFace(MapWritable):

    ObjectName = "side"

    def __init__(self, id = 0, plane = Plane(0, 0, 1, 0), solid = None):
        MapWritable.__init__(self, base.document)
        self.id = id
        self.material = FaceMaterial()
        self.vertices = []
        self.isSelected = False
        self.plane = plane
        self.solid = solid
        self.hasGeometry = False
        self.vdata = None

        # Different primitive representations of this face.
        self.geom3D = None
        self.geom3DLines = None
        self.geom2D = None

        # Index into the Solid's GeomNode of the Geoms we render for this face.
        self.index3D = -1
        self.index3DLines = -1
        self.index2D = -1

        # RenderState for each Geom we render for this face.
        self.state3D = RenderState.makeEmpty()
        self.state3DLines = RenderState.make(AntialiasAttrib.make(AntialiasAttrib.MLine), ColorAttrib.makeFlat(Vec4(1, 1, 0, 1)))
        self.state2D = RenderState.makeEmpty()
        if solid:
            self.setColor(self.solid.color)

        # Not None if face is a displacement.
        self.dispInfo = None

        #self.generateNodes()

    def setPreviewState(self):
        self.state3D = self.state3D.setAttrib(TransparencyAttrib.make(True))
        self.state3D = self.state3D.setAttrib(ColorScaleAttrib.make(Vec4(1, 1, 1, PreviewAlpha)))
        self.state2D = self.state2D.setAttrib(ColorAttrib.makeFlat(LEGlobals.PreviewBrush2DColor))

    def isDisplacement(self):
        return self.dispInfo is not None

    def getBounds(self, other = None):
        return self.solid.getBounds(other)

    def setSolid(self, solid):
        self.solid = solid

    def getOrientation(self):
        plane = self.getWorldPlane()

        # The normal must have a nonzero length!
        if plane[0] == 0 and plane[1] == 0 and plane[2] == 0:
            return FaceOrientation.Invalid

        #
        # Find the axis that the surface normal has the greatest projection onto.
        #

        orientation = FaceOrientation.Invalid
        normal = plane.getNormal()

        maxDot = 0
        for i in range(6):
            dot = normal.dot(FaceNormals[i])

            if (dot >= maxDot):
                maxDot = dot
                orientation = FaceOrientation(i)

        return orientation

    def showClipVisRemove(self):
        self.geom3D.setDraw(False)
        self.state3DLines = self.state3DLines.setAttrib(ColorAttrib.makeFlat(Vec4(1, 0, 0, 1)))
        self.state2D = self.state2D.setAttrib(ColorAttrib.makeFlat(Vec4(1, 0, 0, 1)))
        self.solid.setFaceGeomState(self.geom3DLines, self.state3DLines)
        self.solid.setFaceGeomState(self.geom2D, self.state2D)

    def showClipVisKeep(self):
        self.geom3D.setDraw(True)
        self.state3DLines = self.state3DLines.setAttrib(ColorAttrib.makeFlat(Vec4(1, 1, 0, 1)))
        self.state2D = self.state2D.setAttrib(ColorAttrib.makeFlat(Vec4(1, 1, 1, 1)))
        self.solid.setFaceGeomState(self.geom3DLines, self.state3DLines)
        self.solid.setFaceGeomState(self.geom2D, self.state2D)

    def show3DLines(self):
        if self.geom3DLines:
            self.geom3DLines.setDraw(True)

    def hide3DLines(self):
        if self.geom3DLines:
            self.geom3DLines.setDraw(False)

    def copy(self, generator):
        f = SolidFace(generator.getNextID(), Plane(self.plane), self.solid)
        f.isSelected = self.isSelected
        f.setFaceMaterial(self.material.clone())
        for i in range(len(self.vertices)):
            newVert = self.vertices[i].clone()
            newVert.face = f
            f.vertices.append(newVert)
        return f

    def clone(self):
        f = self.copy(IDGenerator())
        f.id = self.id
        return f

    def paste(self, f):
        self.plane = Plane(f.plane)
        self.isSelected = f.isSelected
        self.setMaterial(f.material.clone())
        self.solid = f.solid
        self.vertices = []
        for i in range(len(f.vertices)):
            newVert = f.vertices[i].clone()
            newVert.face = self
            self.vertices.append(newVert)
        self.generate()

    def unclone(self, f):
        self.paste(f)
        self.id = f.id

    def xform(self, mat):
        for vert in self.vertices:
            vert.xform(mat)
        self.plane.xform(mat)
        self.calcTextureCoordinates(True)
        if self.hasGeometry:
            self.regenerateGeometry()

    def getAbsOrigin(self):
        avg = Point3(0)
        for vert in self.vertices:
            avg += vert.getWorldPos()
        avg /= len(self.vertices)
        return avg

    def getWorldPlane(self):
        plane = Plane(self.plane)
        plane.xform(self.solid.np.getMat(NodePath()))
        return plane

    def getName(self):
        return "Solid face"

    def select(self):
        self.state3D = self.state3D.setAttrib(ColorScaleAttrib.make(Vec4(1, 0.75, 0.75, 1)))
        self.state2D = self.state2D.setAttrib(ColorAttrib.makeFlat(Vec4(1, 0, 0, 1)))
        self.state2D = self.state2D.setAttrib(CullBinAttrib.make("fixed", LEGlobals.SelectedSort))
        self.state2D = self.state2D.setAttrib(DepthWriteAttrib.make(False))
        self.state2D = self.state2D.setAttrib(DepthTestAttrib.make(False))
        self.solid.setFaceGeomState(self.geom3D, self.state3D)
        self.solid.setFaceGeomState(self.geom2D, self.state2D)
        self.show3DLines()
        self.isSelected = True

    def deselect(self):
        self.state3D = self.state3D.removeAttrib(ColorScaleAttrib)
        self.state2D = self.state2D.setAttrib(ColorAttrib.makeFlat(self.solid.color))
        self.state2D = self.state2D.removeAttrib(DepthWriteAttrib)
        self.state2D = self.state2D.removeAttrib(DepthTestAttrib)
        self.state2D = self.state2D.removeAttrib(CullBinAttrib)
        self.solid.setFaceGeomState(self.geom3D, self.state3D)
        self.solid.setFaceGeomState(self.geom2D, self.state2D)
        self.hide3DLines()
        self.isSelected = False

    def readKeyValues(self, kv):
        self.id = int(self.id)
        base.document.reserveFaceID(self.id)

        p0 = Point3()
        p1 = Point3()
        p2 = Point3()
        kv.parsePlanePoints(kv.getValue("plane"), p0, p1, p2)
        self.plane = Plane.fromVertices(p0, p1, p2)

        self.material.readKeyValues(kv)
        self.setMaterial(self.material.material)

    def writeKeyValues(self, kv):
        kv.setKeyValue("id", str(self.id))

        # Write out the first three vertices to define the plane in world space
        vert0 = self.vertices[0].getWorldPos()
        vert1 = self.vertices[1].getWorldPos()
        vert2 = self.vertices[2].getWorldPos()
        kv.setKeyValue("plane", "(%f %f %f) (%f %f %f) (%f %f %f)" % (
            vert0.x, vert0.y, vert0.z,
            vert1.x, vert1.y, vert1.z,
            vert2.x, vert2.y, vert2.z
        ))

        # Write out material values
        self.material.writeKeyValues(kv)

    def generate(self):
        self.regenerateGeometry()

    def setMaterial(self, mat):
        self.material.material = mat
        if mat:
            #self.state3D = self.state3D.setAttrib(BSPMaterialAttrib.make(mat.material))
            self.state3D = self.state3D.setAttrib(TextureAttrib.make(mat.material))
            #if mat.material.hasKeyvalue("$translucent") and bool(int(mat.material.getKeyvalue("$translucent"))):
            #    self.state3D = self.state3D.setAttrib(TransparencyAttrib.make(TransparencyAttrib.MDual))
            if self.geom3D:
                self.solid.setFaceGeomState(self.geom3D, self.state3D)
                #if mat.material.hasKeyvalue("$basetexture") and "tools" in mat.material.getKeyvalue("$basetexture"):
                #    self.geom3D.setDraw(False)

    def setColor(self, color):
        self.state2D = self.state2D.setAttrib(ColorAttrib.makeFlat(color))
        if self.geom2D:
            self.solid.setFaceGeomState(self.geom2D, self.state2D)

    def setFaceMaterial(self, faceMat):
        self.material = faceMat
        self.setMaterial(self.material.material)
        self.calcTextureCoordinates(True)
        self.send('faceMaterialChanged', [self])

    def alignTextureToFace(self):
        self.material.alignTextureToFace(self)
        self.calcTextureCoordinates(True)

    def alignTextureToWorld(self):
        self.material.alignTextureToWorld(self)
        self.calcTextureCoordinates(True)

    def calcTextureCoordinates(self, minimizeShiftValues):
        if minimizeShiftValues:
            self.minimizeTextureShiftValues()

        for vert in self.vertices:
            vert.uv.set(0, 0)

        if self.material.material is None:
            return
        if self.material.material.size.x == 0 or self.material.material.size.y == 0:
            return
        if self.material.scale.x == 0 or self.material.scale.y == 0:
            return

        for vert in self.vertices:
            vertPos = vert.getWorldPos()
            #
            # projected s, t (u, v) texture coordinates
            #
            s = self.material.uAxis.dot(vertPos) / self.material.scale.x + self.material.shift.x
            t = self.material.vAxis.dot(vertPos) / self.material.scale.y + self.material.shift.y

            #
            # "normalize" the texture coordinates
            #
            vert.uv.x = s / self.material.material.size.x
            vert.uv.y = -t / self.material.material.size.y

        self.calcTangentSpaceAxes()

        if self.hasGeometry:
            self.modifyGeometryUVs()

    def calcTangentSpaceAxes(self):
        #
        # Create the axes from texture space axes
        #
        plane = self.getWorldPlane()
        normal = plane.getNormal()
        self.material.binormal = Vec3(self.material.vAxis).normalized()
        self.material.tangent = normal.cross(self.material.binormal).normalized()
        self.material.binormal = self.material.tangent.cross(normal).normalized()

        #
        # Adjust tangent for "backwards" mapping if need be
        #
        tmp = self.material.uAxis.cross(self.material.vAxis)
        if normal.dot(tmp) > 0.0:
            self.material.tangent = -self.material.tangent

    def modifyGeometryUVs(self):
        # Modifies the geometry vertex UVs in-place
        twriter = GeomVertexWriter(self.vdata, InternalName.getTexcoord())
        tanwriter = GeomVertexWriter(self.vdata, InternalName.getTangent())
        bwriter = GeomVertexWriter(self.vdata, InternalName.getBinormal())

        for i in range(len(self.vertices)):
            twriter.setData2f(self.vertices[i].uv)
            tanwriter.setData3f(self.material.tangent)
            bwriter.setData3f(self.material.binormal)

    def minimizeTextureShiftValues(self):
        if self.material.material is None:
            return

        # Keep the shift values to a minimum
        self.material.shift.x %= self.material.material.size.x
        self.material.shift.y %= self.material.material.size.y

        if self.material.shift.x < -self.material.material.size.x / 2:
            self.material.shift.x += self.material.material.size.x
        if self.material.shift.y < -self.material.material.size.y / 2:
            self.material.shift.y += self.material.material.size.y

    def classifyAgainstPlane(self, plane):
        front = back = onplane = 0
        count = len(self.vertices)

        for vert in self.vertices:
            test = plane.onPlane(vert.getWorldPos())
            if test <= 0:
                back += 1
            if test >= 0:
                front += 1
            if test == 0:
                onplane += 1

        if onplane == count:
            return PlaneClassification.OnPlane
        if front == count:
            return PlaneClassification.Front
        if back == count:
            return PlaneClassification.Back
        return PlaneClassification.Spanning

    def flip(self):
        self.vertices.reverse()
        self.plane = Plane.fromVertices(self.vertices[0].pos, self.vertices[1].pos, self.vertices[2].pos)
        if self.hasGeometry:
            self.regenerateGeometry()

    def regenerateGeometry(self):
        #
        # Generate vertex data
        #

        numVerts = len(self.vertices)

        vdata = GeomVertexData("SolidFace", getFaceFormat(), GeomEnums.UHStatic)
        vdata.uncleanSetNumRows(len(self.vertices))

        vwriter = GeomVertexWriter(vdata, InternalName.getVertex())
        twriter = GeomVertexWriter(vdata, InternalName.getTexcoord())
        nwriter = GeomVertexWriter(vdata, InternalName.getNormal())
        tanwriter = GeomVertexWriter(vdata, InternalName.getTangent())
        bwriter = GeomVertexWriter(vdata, InternalName.getBinormal())

        for i in range(len(self.vertices)):
            vert = self.vertices[i]
            vwriter.setData3f(vert.pos)
            twriter.setData2f(vert.uv)
            nwriter.setData3f(self.plane.getNormal())
            tanwriter.setData3f(self.material.tangent)
            bwriter.setData3f(self.material.binormal)

        #
        # Generate indices
        #

        # Triangles in 3D view
        prim3D = GeomTriangles(GeomEnums.UHStatic)
        prim3D.reserveNumVertices((numVerts - 2) * 3)
        for i in range(1, numVerts - 1):
            prim3D.addVertices(i + 1, i, 0)
            prim3D.closePrimitive()

        # Line loop in 2D view.. using line strips
        prim2D = GeomLinestrips(GeomEnums.UHStatic)
        prim2D.reserveNumVertices(numVerts + 1)
        for i in range(numVerts):
            prim2D.addVertex(i)
        # Close off the line strip with the first vertex.. creating a line loop
        prim2D.addVertex(0)
        prim2D.closePrimitive()

        #
        # Generate mesh objects
        #

        geom3D = SolidFaceGeom(vdata)
        geom3D.setDrawMask(VIEWPORT_3D_FULL)
        geom3D.setPlaneCulled(True)
        geom3D.setPlane(self.plane)
        geom3D.addPrimitive(prim3D)
        self.index3D = self.solid.addFaceGeom(geom3D, self.state3D)

        geom3DLines = SolidFaceGeom(vdata)
        geom3DLines.addPrimitive(prim2D)
        geom3DLines.setDrawMask(VIEWPORT_3D_MASK)
        geom3DLines.setDraw(False)
        self.index3DLines = self.solid.addFaceGeom(geom3DLines, self.state3DLines)

        geom2D = SolidFaceGeom(vdata)
        geom2D.addPrimitive(prim2D)
        geom2D.setDrawMask(VIEWPORT_2D_MASK)
        self.index2D = self.solid.addFaceGeom(geom2D, self.state2D)

        self.geom3D = geom3D
        self.geom3DLines = geom3DLines
        self.geom2D = geom2D

        self.vdata = vdata

        self.hasGeometry = True

    def delete(self):
        for vert in self.vertices:
            vert.delete()
        self.vertices = None
        self.id = None
        self.material.cleanup()
        self.material = None
        self.color = None
        self.index2D = None
        self.index3D = None
        self.index3DLines = None
        self.geom3D = None
        self.geom3DLines = None
        self.geom2D = None
        self.state3D = None
        self.state3DLines = None
        self.state2D = None
        self.solid = None
        self.isSelected = None
        self.plane = None
        self.vdata = None
        self.hasGeometry = None
