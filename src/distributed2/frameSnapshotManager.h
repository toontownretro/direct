/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file frameSnapshotManager.h
 * @author brian
 * @date 2020-09-13
 */

#ifndef FRAMESNAPSHOTMANAGER_H
#define FRAMESNAPSHOTMANAGER_H

#include "config_distributed2.h"
#include "packedObject.h"
#include "pmap.h"
#include "extension.h"
#include "datagram.h"

#include "dcbase.h"
#include "datagram.h"
#include "py_panda.h"

class FrameSnapshot;
class DCClass;
class DCField;
class DCPacker;

class FrameSnapshotManager {
PUBLISHED:
  /**
   * Caches the existence of SendProxy methods on a
   * DistributedObject, so we don't have to call PyObject_GetAttrString
   * each time we encode and object state.
   */
  class DOFieldData {
  public:
    DOFieldData() { _send_proxy = nullptr; }
    PyObject *_send_proxy;
    PyObject *_field_name;
  };
  class DOData : public ReferenceCount {
  public:
    DOID_TYPE _do_id;
    DCClass *_dclass;
    PyObject *_dist_obj;
    PyObject *_dict;
    pvector<DOFieldData> _field_data;
  };

  INLINE FrameSnapshotManager();

  PT(PackedObject) create_packed_object(DOID_TYPE do_id);
  PackedObject *get_prev_sent_packet(DOID_TYPE do_id) const;
  void remove_prev_sent_packet(DOID_TYPE do_id);

  void add_object(PyObject *dist_obj);
  void remove_object(DOID_TYPE do_id);

private:
  // The most recently sent packets for each object ID.
  typedef pflat_hash_map<DOID_TYPE, PT(PackedObject), integer_hash<DOID_TYPE>> PrevSentPackets;
  PrevSentPackets _prev_sent_packets;

  typedef pflat_hash_map<DOID_TYPE, PT(DOData), integer_hash<DOID_TYPE>> DODataMap;
  DODataMap _do_data;

private:
  bool encode_object_state(PyObject *dist_obj, DCClass *dclass, DCPacker &packer,
                           PackedObject::PackedFields &fields, DOID_TYPE do_id);

  bool encode_field(PyObject *dist_obj, DCClass *dclass, DCPacker &packer,
                    DCField *field, PackedObject::PackedFields &fields);

PUBLISHED:
  PackedObject *find_or_create_object_packet_for_baseline(PyObject *dist_obj, DCClass *dclass,
                                                          DOID_TYPE do_id);

  bool pack_object_in_snapshot(FrameSnapshot *snapshot, int entry, PyObject *dist_obj,
                               DOID_TYPE do_id, ZONEID_TYPE zone_id, DCClass *dclass);



  void client_format_snapshot(Datagram &dg, FrameSnapshot *snapshot,
                              PyObject *interest_zone_ids);
  void client_format_delta_snapshot(Datagram &dg, FrameSnapshot *from,
                                    FrameSnapshot *to, PyObject *interest_zone_ids);
};

#include "frameSnapshotManager.I"

#endif // FRAMESNAPSHOTMANAGER_H
