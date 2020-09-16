/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file frameSnapshotManager_ext.cxx
 * @author lachbr
 * @date 2020-09-13
 */

#include "frameSnapshotManager_ext.h"
#include "frameSnapshot.h"
#include "frameSnapshotEntry.h"
#include "changeFrameList.h"
#include "packedObject.h"
#include "dcClass.h"
#include "dcPacker.h"
#include "dcField.h"
#include "dcParameter.h"

bool Extension<FrameSnapshotManager>::
pack_object_in_snapshot(FrameSnapshot *snapshot, int entry_idx, PyObject *dist_obj,
                        DOID_TYPE do_id, ZONEID_TYPE zone_id, DCClass *dclass) {
  FrameSnapshotEntry &entry = snapshot->get_entry(entry_idx);
  entry.set_class(dclass);
  entry.set_do_id(do_id);
  entry.set_zone_id(zone_id);
  entry.set_exists(true);

  snapshot->mark_entry_valid(entry_idx);

  //
  // First encode the object's state data
  //

  char proxy_name[256];
  DCPacker packer;
  int num_fields = dclass->get_num_inherited_fields();
  PackedObject::PackedFields packed_fields;
  packed_fields.reserve(num_fields);
  size_t prev_length;
  size_t pos = 0;
  for (int i = 0; i < num_fields; i++) {
    DCField *field = dclass->get_inherited_field(i);
    if (!field) {
      continue;
    }

    // Field must be a parameter, not a method
    DCParameter *param = field->as_parameter();
    if (!param) {
      continue;
    }

    const char *c_name = field->get_name().c_str();

    PyObject *args = nullptr;

    sprintf(proxy_name, "SendProxy_%s", c_name);
    if (PyObject_HasAttrString(dist_obj, proxy_name)) {
      PyObject *proxy = PyObject_GetAttrString(dist_obj, (char *)proxy_name);
      // If we have a proxy, pack the return value.
      args = PyObject_CallObject(proxy, NULL);
      Py_DECREF(proxy);
    } else {
      // If no proxy, pack the physical attribute on the object with the same
      // same as the field.
      if (PyObject_HasAttrString(dist_obj, c_name)) {
        args = PyObject_GetAttrString(dist_obj, (char *)c_name);
      }
    }

    prev_length = packer.get_length();

    packer.begin_pack(field);

    if (args) {
      if (!invoke_extension(field).pack_args(packer, args)) {
        Py_DECREF(args);
        return false;
      }
      if (!packer.end_pack()) {
        Py_DECREF(args);
        return false;
      }

    } else {
      // Try packing a default value if we didn't get args
      packer.pack_default_value();

      if (!packer.end_pack()) {
        return false;
      }
    }

    // Determine how many bytes were just written for this field
    size_t field_length = packer.get_length() - prev_length;

    // Store the location and length of the field in the overall buffer.
    packed_fields.push_back({ i, pos, field_length });
    pos += field_length;
  }

  // Take the bytes out of the packer
  size_t length = packer.get_length();
  const char *data = packer.get_data();

  PT(ChangeFrameList) change_frame = nullptr;

  // If this object was previously in there, then it should have a valid
  // ChangeFrameList which we can delta against to figure out which fields
  // have changed.
  //
  // If not, then we want to set up a new ChangeFrameList.

  PackedObject *prev_pack = _this->get_prev_sent_packet(do_id);
  if (prev_pack) {
    // We have a previously sent packet for this object. Calculate a delta
    // between the state we just packed and this previous state.

    vector_int delta_params;
    int changes = prev_pack->calc_delta(data, length, packed_fields, delta_params);

    if (changes == 0) {
      // If there are no changes between the previous state and the current
      // state, just use the previous state.
      entry.set_packed_object(prev_pack);
      return true;
    }

    // -1 means we can't calculate a delta and all fields should be treated as
    // changed.
    if (changes != -1) {
      // We have changed fields. Snag the ChangeFrameList from the previous
      // packet to store on our new packet.

      // Snag it
      change_frame = prev_pack->take_change_frame_list();
      // Record the deltas
      change_frame->set_change_tick(delta_params.data(), changes, snapshot->get_tick_count());
    }

  } else {
    // We have never sent a packet for this object. Create a new change list.
    change_frame = new ChangeFrameList((int)packed_fields.size(), snapshot->get_tick_count());
  }

  // Now make a PackedObject and store the new packed data in there
  PT(PackedObject) packed_object = _this->create_packed_object(do_id);
  packed_object->set_change_frame_list(change_frame);
  packed_object->set_class(dclass);
  packed_object->set_snapshot_creation_tick(snapshot->get_tick_count());
  packed_object->set_data(packer.take_data(), length);
  packed_object->set_fields(std::move(packed_fields));

  entry.set_packed_object(packed_object);

  return true;
}

void Extension<FrameSnapshotManager>::
client_format_snapshot(Datagram &dg, FrameSnapshot *snapshot,
                       PyObject *py_interest_zone_ids) {
  pvector<ZONEID_TYPE> interest_zone_ids;
  interest_zone_ids.resize(PyList_Size(py_interest_zone_ids));
  for (size_t i = 0; i < interest_zone_ids.size(); i++) {
    interest_zone_ids[i] = PyLong_AsLong(PyList_GetItem(py_interest_zone_ids, i));
  }

  // Record tick count of the snapshot
  dg.add_uint32(snapshot->get_tick_count());

  // Indicate this is *not* a delta snapshot.
  dg.add_uint8(0);

  int num_objects = 0;
  Datagram object_dg;
  for (int i = 0; i < snapshot->get_num_valid_entries(); i++) {
    FrameSnapshotEntry &entry = snapshot->get_entry(snapshot->get_valid_entry(i));
    if (std::find(interest_zone_ids.begin(), interest_zone_ids.end(),
                  entry.get_zone_id()) == interest_zone_ids.end()) {

      // Object not seen by this client, don't include in client snapshot
      continue;
    }

    // Object ID
    object_dg.add_uint32(entry.get_do_id());

    // This is not a delta snapshot, just copy the absolute state
    // onto the datagram.
    PackedObject *packet = entry.get_packed_object();
    int num_fields = packet->get_num_fields();
    object_dg.add_uint16(num_fields);
    for (int j = 0; j < num_fields; j++) {
      const PackedObject::PackedField &field = packet->get_field(j);
      object_dg.add_uint16(field.field_index);
      object_dg.append_data(packet->get_data() + field.offset, field.length);
    }

    num_objects++;
  }

  // # of objects in this client snapshot
  dg.add_uint16(num_objects);

  // Copy object data onto main datagram
  dg.append_data(object_dg.get_data(), object_dg.get_length());
}

void Extension<FrameSnapshotManager>::
client_format_delta_snapshot(Datagram &dg, FrameSnapshot *from, FrameSnapshot *to,
                             PyObject *py_interest_zone_ids) {
  pvector<ZONEID_TYPE> interest_zone_ids;
  interest_zone_ids.resize(PyList_Size(py_interest_zone_ids));
  for (size_t i = 0; i < interest_zone_ids.size(); i++) {
    interest_zone_ids[i] = PyLong_AsLong(PyList_GetItem(py_interest_zone_ids, i));
  }

  // Record tick count of the snapshot
  dg.add_uint32(to->get_tick_count());

  // Indicate this is a delta snapshot.
  dg.add_uint8(1);

  int num_objects = 0;
  Datagram object_dg;
  for (int i = 0; i < to->get_num_valid_entries(); i++) {
    FrameSnapshotEntry &entry = to->get_entry(to->get_valid_entry(i));
    if (std::find(interest_zone_ids.begin(), interest_zone_ids.end(),
                  entry.get_zone_id()) == interest_zone_ids.end()) {

      // Object not seen by this client, don't include in client snapshot
      continue;
    }

    PackedObject *packet = entry.get_packed_object();

    vector_int changed_fields;
    int num_changes = packet->get_fields_changed_after_tick(from->get_tick_count(), changed_fields);

    if (num_changes == 0) {
      // Nothing changed from previous client snapshot, don't include this
      // object.
      continue;
    }

    // Object ID
    object_dg.add_uint32(entry.get_do_id());

    // How many fields are there?
    object_dg.add_uint16(num_changes);

    // Now copy each changed field into the datagram
    for (int j = 0; j < num_changes; j++) {
      const PackedObject::PackedField &field = packet->get_field(changed_fields[j]);
      object_dg.add_uint16(field.field_index);
      object_dg.append_data(packet->get_data() + field.offset, field.length);
    }

    num_objects++;
  }

  // # of objects in this client snapshot
  dg.add_uint16(num_objects);

  // Copy object data onto main datagram
  dg.append_data(object_dg.get_data(), object_dg.get_length());
}
