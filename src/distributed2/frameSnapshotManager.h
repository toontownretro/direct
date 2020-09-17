/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file frameSnapshotManager.h
 * @author lachbr
 * @date 2020-09-13
 */

#ifndef FRAMESNAPSHOTMANAGER_H
#define FRAMESNAPSHOTMANAGER_H

#include "config_distributed2.h"
#include "packedObject.h"
#include "pmap.h"
#include "extension.h"
#include "datagram.h"

class FrameSnapshot;

class EXPCL_DIRECT_DISTRIBUTED2 FrameSnapshotManager {
PUBLISHED:
  INLINE FrameSnapshotManager();

  PT(PackedObject) create_packed_object(DOID_TYPE do_id);
  PackedObject *get_prev_sent_packet(DOID_TYPE do_id) const;
  void remove_prev_sent_packet(DOID_TYPE do_id);

private:
  // The most recently sent packets for each object ID.
  typedef phash_map<DOID_TYPE, PT(PackedObject), integer_hash<DOID_TYPE>> PrevSentPackets;
  PrevSentPackets _prev_sent_packets;

PUBLISHED:
  EXTENSION(PackedObject *find_or_create_object_packet_for_baseline(PyObject *dist_obj, DCClass *dclass,
                                                                    DOID_TYPE do_id));
  EXTENSION(void client_format_snapshot(Datagram &dg, FrameSnapshot *snapshot,
                                        PyObject *interest_zone_ids));
  EXTENSION(void client_format_delta_snapshot(Datagram &dg, FrameSnapshot *from,
                                              FrameSnapshot *to, PyObject *interest_zone_ids));

  EXTENSION(bool pack_object_in_snapshot(FrameSnapshot *snapshot, int entry, PyObject *dist_obj,
                                         DOID_TYPE do_id, ZONEID_TYPE zone_id, DCClass *dclass));


  friend class Extension<FrameSnapshotManager>;
};

#include "frameSnapshotManager.I"

#endif // FRAMESNAPSHOTMANAGER_H
