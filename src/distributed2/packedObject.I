/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file packedObject.I
 * @author brian
 * @date 2020-09-13
 */

/**
 *
 */
INLINE PackedObject::
PackedObject() {
  _data = nullptr;
  _length = 0;
  _dclass = nullptr;
  _do_id = 0;
  _change_frame_list = nullptr;
  _creation_tick = 0;
  _should_check_creation_tick = false;
#ifdef DO_MEMORY_USAGE
  MemoryUsage::update_type(this, this);
#endif
}

/**
 *
 */
INLINE void PackedObject::
set_data(char *data, size_t length) {
  clear_data();
  _data = data;
  _length = length;
}

/**
 *
 */
INLINE void PackedObject::
clear_data() {
  if (_data != nullptr) {
    delete[] _data;
    _data = nullptr;
  }
  _length = 0;
  _fields.clear();
}

/**
 *
 */
INLINE const char *PackedObject::
get_data() const {
  return _data;
}

/**
 *
 */
INLINE size_t PackedObject::
get_length() const {
  return _length;
}

/**
 *
 */
INLINE void PackedObject::
set_fields(PackedObject::PackedFields &&fields) {
  _fields = std::move(fields);
}

/**
 *
 */
INLINE void PackedObject::
set_fields(const PackedObject::PackedFields &fields) {
  _fields = fields;
}

/**
 *
 */
INLINE const PackedObject::PackedField &PackedObject::
get_field(int n) const {
  return _fields[n];
}

/**
 *
 */
INLINE int PackedObject::
get_num_fields() const {
  return (int)_fields.size();
}

/**
 * Sets the tick that the PackedObject was created on.
 */
INLINE void PackedObject::
set_snapshot_creation_tick(int tick) {
  _creation_tick = tick;
}

/**
 * Returns the tick that the PackedObject was created on.
 */
INLINE int PackedObject::
get_snapshot_creation_tick() const {
  return _creation_tick;
}

/**
 * Sets the DCClass this PackedObject represents.
 */
INLINE void PackedObject::
set_class(DCClass *dclass) {
  _dclass = dclass;
}

/**
 * Returns the DCClass this PackedObject represents.
 */
INLINE DCClass *PackedObject::
get_class() const {
  return _dclass;
}

/**
 *
 */
INLINE void PackedObject::
set_do_id(DOID_TYPE do_id) {
  _do_id = do_id;
}

/**
 *
 */
INLINE DOID_TYPE PackedObject::
get_do_id() const {
  return _do_id;
}

/**
 *
 */
INLINE void PackedObject::
set_change_frame_list(ChangeFrameList *list) {
  _change_frame_list = list;
}

/**
 *
 */
INLINE ChangeFrameList *PackedObject::
get_change_frame_list() const {
  return _change_frame_list;
}

/**
 * Transfers ownership of the ChangeFrameList to the caller.
 */
INLINE PT(ChangeFrameList) PackedObject::
take_change_frame_list() {
  PT(ChangeFrameList) list = _change_frame_list;
  _change_frame_list = nullptr;
  return list;
}

/**
 *
 */
INLINE int PackedObject::
get_fields_changed_after_tick(int tick, vector_int &out_fields) {
  if (_change_frame_list) {
    return _change_frame_list->get_fields_changed_after_tick(tick, out_fields);
  } else {
    // Signal that we don't have a change list
    return -1;
  }
}
