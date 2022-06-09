/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file cClientRepository.I
 * @author lachbr
 * @date 2020-09-15
 */

/**
 *
 */
INLINE CClientRepository::
CClientRepository() {
  _py_repo = nullptr;
}


/**
 * Sets the Python ClientRepository. The `doId2do` dictionary will be queried
 * on this object.
 */
INLINE void CClientRepository::
set_python_repository(PyObject *repo) {
  Py_XDECREF(_py_repo);
  _py_repo = repo;
  Py_XINCREF(_py_repo);
}

/**
 *
 */
INLINE bool CClientRepository::
unpack_object_state(DatagramIterator &scan, DOID_TYPE do_id) {
  DODataMap::const_iterator it = _do_data.find(do_id);
  if (it == _do_data.end()) {
    return false;
  }
  return unpack_object_state(scan, (*it).second);
}
