/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file config_actor.cxx
 * @author drose
 * @date 2004-05-19
 */

#include "config_actor.h"
#include "dconfig.h"

#if !defined(CPPPARSER) && !defined(LINK_ALL_STATIC) && !defined(BUILDING_DIRECT_ACTOR)
  #error Buildsystem error: BUILDING_DIRECT_ACTOR not defined
#endif

Configure(config_actor);
NotifyCategoryDef(actor, "");

ConfigureFn(config_actor) {
  init_libactor();
}

/**
 * Initializes the library.  This must be called at least once before any of
 * the functions or classes in this library can be used.  Normally it will be
 * called by the static initializers and need not be called explicitly, but
 * special cases exist.
 */
void
init_libactor() {
  static bool initialized = false;
  if (initialized) {
    return;
  }
  initialized = true;

}