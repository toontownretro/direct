/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file frameSnapshotEntry.h
 * @author brian
 * @date 2020-09-13
 */

/**
 *
 */
INLINE FrameSnapshotEntry::
FrameSnapshotEntry() {
  _dclass = nullptr;
  _packed_data = nullptr;
  _do_id = 0;
  _zone_id = 0;
  _exists = false;
}

/**
 *
 */
INLINE void FrameSnapshotEntry::
set_class(DCClass *dclass) {
  _dclass = dclass;
}

/**
 *
 */
INLINE DCClass *FrameSnapshotEntry::
get_class() const {
  return _dclass;
}

/**
 *
 */
INLINE void FrameSnapshotEntry::
set_do_id(DOID_TYPE do_id) {
  _do_id = do_id;
}

/**
 *
 */
INLINE DOID_TYPE FrameSnapshotEntry::
get_do_id() const {
  return _do_id;
}

/**
 *
 */
INLINE void FrameSnapshotEntry::
set_zone_id(ZONEID_TYPE zone_id) {
  _zone_id = zone_id;
}

/**
 *
 */
INLINE ZONEID_TYPE FrameSnapshotEntry::
get_zone_id() const {
  return _zone_id;
}

/**
 *
 */
INLINE void FrameSnapshotEntry::
set_exists(bool exists) {
  _exists = exists;
}

/**
 *
 */
INLINE bool FrameSnapshotEntry::
get_exists() const {
  return _exists;
}

/**
 *
 */
INLINE void FrameSnapshotEntry::
set_packed_object(PackedObject *obj) {
  _packed_data = obj;
}

/**
 *
 */
INLINE PackedObject *FrameSnapshotEntry::
get_packed_object() const {
  return _packed_data;
}
