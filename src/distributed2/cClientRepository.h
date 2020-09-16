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
#include "py_panda.h"

class DCClass;

/**
 * This is the C++ implementation of the ClientRepository, which currently
 * only handles unpacking of server snapshots and object state datagrams
 * for performance efficiency.
 */
class EXPCL_DIRECT_DISTRIBUTED2 CClientRepository {
PUBLISHED:
  INLINE CClientRepository();

  INLINE void set_python_repository(PyObject *repo);

  void unpack_server_snapshot(DatagramIterator &dgi);
  bool unpack_object_state(DatagramIterator &dgi, PyObject *dist_obj,
                           DCClass *dclass, DOID_TYPE do_id);

private:
  PyObject *_py_repo;
};

#include "cClientRepository.I"

#endif // CCLIENTREPOSITORY_H
