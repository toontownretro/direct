#include "solidGeomNode.h"
#include "cullTraverser.h"
#include "cullTraverserData.h"
#include "cullableObject.h"
#include "cullHandler.h"

IMPLEMENT_CLASS(SolidGeomNode);

void SolidGeomNode::
add_for_draw(CullTraverser *trav, CullTraverserData &data) {
  trav->_geom_nodes_pcollector.add_level(1);

  Thread *current_thread = trav->get_current_thread();

  BitMask32 mask = trav->get_camera_mask();

  // Get all the Geoms, with no decalling.
  Geoms geoms = get_geoms(current_thread);
  int num_geoms = geoms.get_num_geoms();
  trav->_geoms_pcollector.add_level(num_geoms);
  CPT(TransformState) internal_transform = data.get_internal_transform(trav);

  const TransformState *net_node = nullptr;
  const TransformState *cam = nullptr;

  for (int i = 0; i < num_geoms; i++) {
    CPT(SolidFaceGeom) geom = DCAST(SolidFaceGeom, geoms.get_geom(i));
    if (geom->is_empty()) {
      continue;
    }

    if ((geom->get_draw_mask() & mask) == 0) {
      // Geom not seen by this camera.
      continue;
    }

    if (!geom->should_draw()) {
      continue;
    }

    if (geom->is_plane_culled()) {
      // Only calculate this if we haven't yet.
      if (!net_node) {
        net_node = data.get_net_transform(trav);
        cam = net_node->invert_compose(trav->get_camera_transform());
      }
      // If camera is behind the plane, cull.
      if (geom->get_plane().dist_to_plane(cam->get_pos()) <= 0.0f) {
        continue;
      }
    }

    CPT(RenderState) state = data._state->compose(geoms.get_geom_state(i));
    if (state->has_cull_callback() && !state->cull_callback(trav, data)) {
      // Cull.
      continue;
    }

    CullableObject *object =
      new CullableObject(std::move(geom), std::move(state), internal_transform);
    trav->get_cull_handler()->record_object(object, trav);
  }
}
