#include "config_foundry.h"
#include "solidGeomNode.h"

NotifyCategoryDef(foundry, "");

ConfigureDef(config_foundry);
ConfigureFn(config_foundry) {
  init_libfoundry();
}

void
init_libfoundry() {
  static bool initialized = false;
  if (initialized) {
    return;
  }

  initialized = true;

  SolidGeomNode::init_type();
}
