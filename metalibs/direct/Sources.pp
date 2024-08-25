// DIR_TYPE "metalib" indicates we are building a shared library that
// consists mostly of references to other shared libraries.  Under
// Windows, this directly produces a DLL (as opposed to the regular
// src libraries, which don't produce anything but a pile of OBJ files
// under Windows).

#define DIR_TYPE metalib

#if $[BUILD_COMPONENTS]
#define BUILDING_DLL BUILDING_DIRECT_STUB
#else
#define BUILDING_DLL BUILDING_DIRECT
#endif

#define USE_PACKAGES native_net

#define COMPONENT_LIBS \
  actor directbase dcparser showbase deadrec directd interval distributed motiontrail http \
  dxml distributed2 foundry

#define OTHER_LIBS \
  panda:m \
  pandaexpress:m \
  parametrics:c \
  interrogatedb  \
  dtoolutil:c dtoolbase:c dtool:m \
  express:c pstatclient:c prc linmath:c \
  putil:c display:c event:c pgraph:c pgraphnodes:c \
  gsgbase:c gobj:c mathutil:c \
  downloader:c pnmimage:c anim:c \
  pipeline:c cull:c \
  $[if $[HAVE_NET],net:c] $[if $[WANT_NATIVE_NET],nativenet:c]

#begin metalib_target
  #define TARGET direct

  #define SOURCES direct.cxx
#end metalib_target
