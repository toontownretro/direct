/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file config_actor.h
 * @author drose
 * @date 2004-05-19
 */

#ifndef CONFIG_ACTOR_H
#define CONFIG_ACTOR_H

#include "directbase.h"
#include "notifyCategoryProxy.h"
#include "dconfig.h"
#include "configVariableInt.h"
#include "configVariableDouble.h"
#include "configVariableBool.h"

NotifyCategoryDecl(actor, EXPCL_DIRECT_ACTOR, EXPTP_DIRECT_ACTOR);

extern EXPCL_DIRECT_ACTOR void init_libactor();

#endif