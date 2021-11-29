/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file cClientRepository.h
 * @author lachbr
 * @date 2020-09-15
 */

#ifndef CCLIENTREPOSITORY_H
#define CCLIENTREPOSITORY_H

#include "config_distributed2.h"
#include "datagramIterator.h"
#include "dcbase.h"
#include "pmap.h"
#include "py_panda.h"

class DCClass;

/**
 * This is the C++ implementation of the ClientRepository, which currently
 * only handles unpacking of server snapshots and object state datagrams
 * for performance efficiency.
 */
class CClientRepository {
PUBLISHED:
  /**
   * Caches the existence of RecvProxy/PostDataUpdate methods on a
   * DistributedObject, so we don't have to call PyObject_GetAttrString
   * each time we unpack an object state.
   */
  class DOFieldData {
  public:
    DOFieldData() { _recv_proxy = nullptr; }
    PyObject *_recv_proxy;
  };
  class DOData : public ReferenceCount {
  public:
    DOID_TYPE _do_id;
    DCClass *_dclass;
    PyObject *_dist_obj;
    PyObject *_pre_data_update;
    PyObject *_post_data_update;
    PyObject *_on_data_changed;
    pvector<DOFieldData> _field_data;
  };

  INLINE CClientRepository();

  INLINE void set_python_repository(PyObject *repo);

  void unpack_server_snapshot(DatagramIterator &dgi, bool is_delta);
  bool unpack_object_state(DatagramIterator &dgi, DOID_TYPE do_id);

  void add_object(PyObject *dist_obj);
  void remove_object(DOID_TYPE do_id);

private:
  PyObject *_py_repo;
  typedef pflat_hash_map<DOID_TYPE, PT(DOData), integer_hash<DOID_TYPE>> DODataMap;
  DODataMap _do_data;
};

#include "cClientRepository.I"

#endif // CCLIENTREPOSITORY_H
