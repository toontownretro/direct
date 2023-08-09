#define INSTALL_CONFIG \
  $[ODIR_GEN]/40_direct.prc direct.fgd

#if $[CTPROJS]
  // These files only matter to ctattach users.
  #define INSTALL_CONFIG $[INSTALL_CONFIG] direct.init
#endif


#include $[THISDIRPREFIX]direct.prc.pp
