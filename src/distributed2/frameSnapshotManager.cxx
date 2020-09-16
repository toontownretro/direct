/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file frameSnapshotManager.cxx
 * @author lachbr
 * @date 2020-09-13
 */

#include "frameSnapshotManager.h"
#include "frameSnapshot.h"

/**
 * Creates and returns a new PackedObject for the specified object ID.
 */
PT(PackedObject) FrameSnapshotManager::
create_packed_object(DOID_TYPE do_id) {
  PT(PackedObject) obj = new PackedObject;
  obj->set_do_id(do_id);
  _prev_sent_packets[do_id] = obj;
  return obj;
}

/**
 * Returns the most recently sent packed state for the specified object ID, or
 * nullptr if no packet was ever sent for the object.
 */
PackedObject *FrameSnapshotManager::
get_prev_sent_packet(DOID_TYPE do_id) const {
  auto itr = _prev_sent_packets.find(do_id);
  if (itr != _prev_sent_packets.end()) {
    return itr->second;
  }

  return nullptr;
}

/**
 * Removes the most recently packed state for the specified object ID from the
 * cache. Call this when the object is being deleted so that a possible future
 * object with the same ID does not use this state!
 */
void FrameSnapshotManager::
remove_prev_sent_packet(DOID_TYPE do_id) {
  auto itr = _prev_sent_packets.find(do_id);
  if (itr != _prev_sent_packets.end()) {
    _prev_sent_packets.erase(itr);
  }
}
