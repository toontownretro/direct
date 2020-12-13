#ifndef PLANECULLEDGEOMNODE_H
#define PLANECULLEDGEOMNODE_H

#include "config_foundry.h"
#include "geomNode.h"
#include "luse.h"
#include "plane.h"

/**
 * A GeomNode that is culled based on a specified plane.
 * If the camera is behind the plane, the node is culled.
 */
class EXPCL_DIRECT_FOUNDRY PlaneCulledGeomNode : public GeomNode {
  DECLARE_CLASS(PlaneCulledGeomNode, GeomNode)

PUBLISHED:
  PlaneCulledGeomNode(const std::string &name);

  void set_plane(const LPlane &plane);
  LPlane get_plane() const;

protected:
  virtual bool cull_callback(CullTraverser *trav, CullTraverserData &data);

private:
  LPlane _plane;
};

INLINE PlaneCulledGeomNode::
PlaneCulledGeomNode(const std::string &name) :
  GeomNode(name),
  _plane(0, 0, 1, 0) {

  set_cull_callback();
}

INLINE void PlaneCulledGeomNode::
set_plane(const LPlane &plane) {
  _plane = plane;
}

INLINE LPlane PlaneCulledGeomNode::
get_plane() const {
  return _plane;
}

#endif // PLANECULLEDGEOMNODE_H
