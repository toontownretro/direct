/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file frameSnapshot.cxx
 * @author brian
 * @date 2020-09-15
 */

#include "frameSnapshot.h"

TypeHandle FrameSnapshot::_type_handle;

/**
 *
 */
FrameSnapshot::
~FrameSnapshot() {
  if (_entries != nullptr) {
    delete[] _entries;
    _entries = nullptr;
  }
}
