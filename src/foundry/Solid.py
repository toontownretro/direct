from panda3d.core import Point3, Vec3, NodePath, KeyValues, CollisionNode, CollisionPolygon, CollisionSegment, Vec4, Mat4
from panda3d.direct import SolidGeomNode

from direct.foundry.Winding import Winding
from .MapObject import MapObject
from .SolidFace import SolidFace
from .SolidVertex import SolidVertex

from direct.foundry import LEUtils, LEGlobals
from direct.foundry import PlaneClassification
from direct.foundry.Plane import Plane

from .ObjectProperty import ObjectProperty

import sys
import random

class VisOccluder(ObjectProperty):

    def __init__(self, mapObject):
        ObjectProperty.__init__(self, mapObject)
        self.valueType = "boolean"
        self.value = True
        self.defaultValue = True
        self.name = "visoccluder"

    def clone(self, mapObject):
        prop = VisOccluder(mapObject)
        self.copyBase(prop)
        return prop

    def getDescription(self):
        return "Turn this on to make the Solid block visibility of other objects."

    def getDisplayName(self):
        return "Vis Occluder"

# A brush
class Solid(MapObject):

    ObjectName = "solid"

    def __init__(self, id):
        MapObject.__init__(self, id)
        self.np = NodePath(SolidGeomNode("solid.%i" % id))
        self.np.setPythonTag("mapobject", self)
        self.np.node().setFinal(True)

        self.coll3D = self.np.attachNewNode(CollisionNode("coll3D"))
        self.coll3D.setCollideMask(LEGlobals.ObjectMask | LEGlobals.FaceMask | LEGlobals.Mask3D)
        #self.coll2D = self.np.attachNewNode(CollisionNode("coll2D"))
        #self.coll2D.setCollideMask(LEGlobals.ObjectMask | LEGlobals.FaceMask | LEGlobals.Mask2D)

        # CollisionSolid -> SolidFace
        self.faceCollSolids = {}

        self.geomIndices = {}
        self.faces = []

        self.pickRandomColor()

        self.addProperty(VisOccluder(self))

    def shouldWriteTransform(self):
        return False

    def pickRandomColor(self):
        # Picks a random shade of blue/green for this solid.
        self.setColor(LEUtils.getRandomSolidColor())

    def setColor(self, color):
        self.color = color
        for face in self.faces:
            face.setColor(color)

    def getFaceFromCollisionSolid(self, solid):
        return self.faceCollSolids[solid]

    def addFaceGeom(self, geom, state):
        index = self.np.node().getNumGeoms()
        self.geomIndices[geom] = index
        self.np.node().addGeom(geom, state)
        return index

    def setFaceGeomState(self, geom, state):
        index = self.geomIndices[geom]
        self.np.node().setGeomState(index, state)

    def alignTexturesToFaces(self):
        for face in self.faces:
            face.alignTextureToFace()

    def alignTexturesToWorld(self):
        for face in self.faces:
            face.alignTextureToWorld()

    def copy(self, generator):
        s = Solid(generator.getNextID())
        self.copyBase(s, generator)
        for face in self.faces:
            f = face.copy(generator)
            f.setSolid(s)
            s.faces.append(f)
        s.generateFaces()
        return s

    def generateFaces(self):
        for face in self.faces:
            face.generate()
        if not self.temporary:
            self.createFaceCollisions()

    def writeKeyValues(self, keyvalues):
        MapObject.writeKeyValues(self, keyvalues)

        # Write or faces or "sides"
        for face in self.faces:
            faceKv = KeyValues("side", keyvalues)
            face.writeKeyValues(faceKv)

    def readKeyValues(self, kv):
        MapObject.readKeyValues(self, kv)

        numChildren = kv.getNumChildren()
        for i in range(numChildren):
            child = kv.getChild(i)
            if child.getName() == "side":
                face = SolidFace(solid = self)
                face.readKeyValues(child)
                self.faces.append(face)

        self.createVerticesFromFacePlanes()
        self.setToSolidOrigin()
        self.generateFaces()
        self.createFaceCollisions()

    # Creates the collision objects that will be tested against for selecting solid faces.
    def createFaceCollisions(self):
        self.coll3D.node().clearSolids()
        #self.coll2D.node().clearSolids()

        self.faceCollSolids = {}

        for face in self.faces:

            numVerts = len(face.vertices)

            # Tris in 3D for ray->face selection
            for i in range(1, numVerts - 1):
                poly = CollisionPolygon(face.vertices[i+1].pos, face.vertices[i].pos, face.vertices[0].pos)
                self.coll3D.node().addSolid(poly)
                self.faceCollSolids[poly] = face

            # Lines in 2D for box->edge selection
            #for i in range(len(face.vertices)):
            #    a = face.vertices[i].pos
            #    b = face.vertices[(i+1) % numVerts].pos
            #    if a == b:
            #        continue
            #    segment = CollisionSegment(a, b)
            #    self.coll2D.node().addSolid(segment)
            #    self.faceCollSolids[face][1].append(segment)

    def createVerticesFromFacePlanes(self):
        for i in range(len(self.faces)):
            face = self.faces[i]
            w = Winding.fromPlaneAndRadius(face.plane)

            for j in range(len(self.faces)):
                if i == j:
                    continue
                other = self.faces[j]
                #
                # Flip the plane, because we want to keep the back side.
                #
                w.splitInPlace(-other.plane)
            w.roundPoints()
            # The final winding is the face
            for j in range(len(w.vertices)):
                face.vertices.append(SolidVertex(w.vertices[j], face))
            face.calcTextureCoordinates(True)

    def showClipVisRemove(self):
        for face in self.faces:
            face.showClipVisRemove()

    def showClipVisKeep(self):
        for face in self.faces:
            face.showClipVisKeep()

    def showBoundingBox(self):
        for face in self.faces:
            face.show3DLines()

    def hideBoundingBox(self):
        for face in self.faces:
            face.hide3DLines()

    def select(self):
        MapObject.select(self)
        for face in self.faces:
            face.select()

    def deselect(self):
        MapObject.deselect(self)
        for face in self.faces:
            face.deselect()

    def getAbsSolidOrigin(self):
        avg = Point3(0)
        for face in self.faces:
            avg += face.getAbsOrigin()
        avg /= len(self.faces)
        return avg

    def setToSolidOrigin(self):
        # Moves the solid origin to median of all face vertex positions,
        # and transforms all faces to be relative to the median position.
        # Resets angles, scale, and shear.
        origin = self.getAbsSolidOrigin()
        self.setAbsOrigin(origin)
        self.setAbsAngles(Vec3(0))
        self.setAbsScale(Vec3(1))
        self.setAbsShear(Vec3(0))
        mat = self.np.getMat(NodePath())
        mat.invertInPlace()
        for face in self.faces:
            face.xform(mat)

    def getName(self):
        return "Solid"

    def getDescription(self):
        return "Convex solid geometry."

    def delete(self):
        MapObject.delete(self)
        self.coll3D.removeNode()
        self.coll3D = None
        #self.coll2D.removeNode()
        #self.coll2D = None
        self.faceCollSolids = None
        for face in self.faces:
            face.delete()
        self.faces = None
        self.color = None

    # Splits this solid into two solids by intersecting against a plane.
    def split(self, plane, generator, temp = False):
        back = front = None

        # Check that this solid actually spans the plane
        classifications = []
        for face in self.faces:
            classify = face.classifyAgainstPlane(plane)
            if classify not in classifications:
                classifications.append(classify)
        if PlaneClassification.Spanning not in classifications:
            if PlaneClassification.Back in classifications:
                back = self
            elif PlaneClassification.Front in classifications:
                front = self
            return [False, back, front]

        backPlanes = [plane]
        flippedFront = Plane(plane)
        flippedFront.flip()
        frontPlanes = [flippedFront]

        for face in self.faces:
            classify = face.classifyAgainstPlane(plane)
            if classify != PlaneClassification.Back:
                frontPlanes.append(face.getWorldPlane())
            if classify != PlaneClassification.Front:
                backPlanes.append(face.getWorldPlane())

        back = Solid.createFromIntersectingPlanes(backPlanes, generator, False, temp)
        front = Solid.createFromIntersectingPlanes(frontPlanes, generator, False, temp)
        if not temp:
            # copyBase() will set the transform to what we're copying from, but we already
            # figured out a transform for the solids. Store the current transform so we can
            # set it back.
            bTrans = back.np.getTransform()
            fTrans = front.np.getTransform()
            self.copyBase(back, generator)
            self.copyBase(front, generator)
            back.np.setTransform(bTrans)
            front.np.setTransform(fTrans)

        unionOfFaces = front.faces + back.faces
        for face in unionOfFaces:
            face.material = self.faces[0].material.clone()
            face.setMaterial(face.material.material)
            face.alignTextureToFace()

        # Restore textures (match the planes up on each face)
        for orig in self.faces:
            for face in back.faces:
                classify = face.classifyAgainstPlane(orig.getWorldPlane())
                if classify != PlaneClassification.OnPlane:
                    continue
                face.material = orig.material.clone()
                face.setMaterial(face.material.material)
                face.alignTextureToFace()
                break
            for face in front.faces:
                classify = face.classifyAgainstPlane(orig.getWorldPlane())
                if classify != PlaneClassification.OnPlane:
                    continue
                face.material = orig.material.clone()
                face.setMaterial(face.material.material)
                face.alignTextureToFace()
                break

        back.generateFaces()
        front.generateFaces()

        if not temp:
            back.recalcBoundingBox()
            front.recalcBoundingBox()

        return [True, back, front]

    @staticmethod
    def createFromIntersectingPlanes(planes, generator, generateFaces = True, temp = False):
        solid = Solid(generator.getNextID())
        solid.setTemporary(temp)
        for i in range(len(planes)):
            # Split the winding by all the other planes
            w = Winding.fromPlaneAndRadius(planes[i])
            for j in range(len(planes)):
                if i != j:
                    # Flip the plane, because we want to keep the back.
                    w.splitInPlace(-planes[j])

            # Round vertices a bit for sanity
            w.roundPoints()

            # The final winding is the face
            face = SolidFace(generator.getNextFaceID(), Plane(planes[i]), solid)
            for j in range(len(w.vertices)):
                face.vertices.append(SolidVertex(w.vertices[j], face))
            solid.faces.append(face)

        if not temp:
            solid.setToSolidOrigin()

            # Ensure all faces point outwards
            origin = Point3(0)
            for face in solid.faces:
                # The solid origin should be on or behind the face plane.
                # If the solid origin is in front of the face plane, flip the face.
                if face.plane.distToPlane(origin) > 0:
                    face.flip()

        if generateFaces:
            solid.alignTexturesToFaces()
            solid.generateFaces()
            if not temp:
                solid.recalcBoundingBox()

        return solid
