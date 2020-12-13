#include "planeCulledGeomNode.h"
#include "cullTraverserData.h"

IMPLEMENT_CLASS(PlaneCulledGeomNode)

bool PlaneCulledGeomNode::
cull_callback(CullTraverser *trav, CullTraverserData &data) {
  const TransformState *net_node = data.get_net_transform(trav);
  const TransformState *cam = net_node->invert_compose(trav->get_camera_transform());

  // If the camera is behind the plane, cull.
  if (_plane.dist_to_plane(cam->get_pos()) <= 0.0f) {
    return false;
  }

  return true;
}
