/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file frameSnapshotManager_ext.h
 * @author lachbr
 * @date 2020-09-13
 */

#ifndef FRAMESNAPSHOTMANAGER_EXT_H
#define FRAMESNAPSHOTMANAGER_EXT_H

#include "frameSnapshotManager.h"
#include "extension.h"
#include "dcbase.h"
#include "datagram.h"
#include "py_panda.h"

class FrameSnapshot;
class DCClass;

template<>
class Extension<FrameSnapshotManager> : public ExtensionBase<FrameSnapshotManager> {
private:
  bool encode_object_state(PyObject *dist_obj, DCClass *dclass, DCPacker &packer,
                           PackedObject::PackedFields &fields);

public:
  PackedObject *find_or_create_object_packet_for_baseline(PyObject *dist_obj, DCClass *dclass,
                                                          DOID_TYPE do_id);

  bool pack_object_in_snapshot(FrameSnapshot *snapshot, int entry, PyObject *dist_obj,
                               DOID_TYPE do_id, ZONEID_TYPE zone_id, DCClass *dclass);



  void client_format_snapshot(Datagram &dg, FrameSnapshot *snapshot,
                              PyObject *interest_zone_ids);
  void client_format_delta_snapshot(Datagram &dg, FrameSnapshot *from,
                                    FrameSnapshot *to, PyObject *interest_zone_ids);
};

#endif // FRAMESNAPSHOTMANAGER_EXT_H
