#ifndef CONFIG_FOUNDRY_H
#define CONFIG_FOUNDRY_H

#include "dconfig.h"
#include "directbase.h"
#include "notifyCategoryProxy.h"

NotifyCategoryDecl(foundry, EXPCL_DIRECT_FOUNDRY, EXPTP_DIRECT_FOUNDRY);
ConfigureDecl(config_foundry, EXPCL_DIRECT_FOUNDRY, EXPTP_DIRECT_FOUNDRY);

extern EXPCL_DIRECT_FOUNDRY void init_libfoundry();

#endif // CONFIG_FOUNDRY_H
