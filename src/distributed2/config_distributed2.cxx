/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file config_distributed2.cxx
 * @author lachbr
 * @date 2020-09-13
 */

#include "config_distributed2.h"
#include "dconfig.h"

#include "packedObject.h"
#include "clientFrame.h"
#include "frameSnapshot.h"
#include "frameSnapshotEntry.h"

#if !defined(CPPPARSER) && !defined(LINK_ALL_STATIC) && !defined(BUILDING_DIRECT_DISTRIBUTED2)
  #error Buildsystem error: BUILDING_DIRECT_DISTRIBUTED2 not defined
#endif

Configure(config_distributed2);
NotifyCategoryDef(distributed2, "");

ConfigureFn(config_distributed2) {
  init_libdistributed2();
}

/**
 * Initializes the library.  This must be called at least once before any of
 * the functions or classes in this library can be used.  Normally it will be
 * called by the static initializers and need not be called explicitly, but
 * special cases exist.
 */
void
init_libdistributed2() {
  static bool initialized = false;
  if (initialized) {
    return;
  }
  initialized = true;

  ClientFrame::init_type();
  FrameSnapshot::init_type();
  FrameSnapshotEntry::init_type();
  PackedObject::init_type();
}
