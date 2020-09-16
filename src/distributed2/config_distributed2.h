/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file config_distributed2.h
 * @author lachbr
 * @date 2020-09-13
 */

#ifndef CONFIG_DISTRIBUTED2_H
#define CONFIG_DISTRIBUTED2_H

#include "directbase.h"
#include "notifyCategoryProxy.h"
#include "dconfig.h"

NotifyCategoryDecl(distributed2, EXPCL_DIRECT_DISTRIBUTED2, EXPTP_DIRECT_DISTRIBUTED2);

extern EXPCL_DIRECT_DISTRIBUTED void init_libdistributed2();

#endif
