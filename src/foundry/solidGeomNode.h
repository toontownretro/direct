#ifndef SOLIDGEOMNODE_H
#define SOLIDGEOMNODE_H

#include "config_foundry.h"
#include "geomNode.h"
#include "geom.h"
#include "bitMask.h"
#include "plane.h"

class EXPCL_DIRECT_FOUNDRY SolidFaceGeom : public Geom {
public:
  ALLOC_DELETED_CHAIN(SolidFaceGeom);

PUBLISHED:
  SolidFaceGeom(const GeomVertexData *vertex_data);

  void set_plane_culled(bool cull);
  void set_plane(const LPlane &plane);
  void set_draw_mask(const BitMask32 &mask);
  void set_draw(bool draw);

  bool should_draw() const;
  BitMask32 get_draw_mask() const;
  bool is_plane_culled() const;
  const LPlane &get_plane() const;

private:
  bool _draw;
  bool _plane_culled;
  BitMask32 _draw_mask;
  LPlane _plane;
};

INLINE SolidFaceGeom::
SolidFaceGeom(const GeomVertexData *vertex_data) :
  Geom(vertex_data) {

  _draw = true;
  _plane_culled = false;
  _draw_mask = BitMask32::all_on();
}

INLINE void SolidFaceGeom::
set_plane_culled(bool cull) {
  _plane_culled = cull;
}

INLINE void SolidFaceGeom::
set_plane(const LPlane &plane) {
  _plane = plane;
}

INLINE void SolidFaceGeom::
set_draw_mask(const BitMask32 &mask) {
  _draw_mask = mask;
}

INLINE void SolidFaceGeom::
set_draw(bool draw) {
  _draw = draw;
}

INLINE bool SolidFaceGeom::
should_draw() const {
  return _draw;
}

INLINE BitMask32 SolidFaceGeom::
get_draw_mask() const {
  return _draw_mask;
}

INLINE bool SolidFaceGeom::
is_plane_culled() const {
  return _plane_culled;
}

INLINE const LPlane &SolidFaceGeom::
get_plane() const {
  return _plane;
}

class EXPCL_DIRECT_FOUNDRY SolidGeomNode : public GeomNode {
  DECLARE_CLASS(SolidGeomNode, GeomNode);

PUBLISHED:
  SolidGeomNode(const std::string &name);

public:
  virtual void add_for_draw(CullTraverser *trav, CullTraverserData &data);
};

INLINE SolidGeomNode::
SolidGeomNode(const std::string &name) :
  GeomNode(name) {
}

#endif // SOLIDGEOMNODE_H
