#begin lib_target
  #define TARGET motiontrail
  #define LOCAL_LIBS \
    directbase

  #define BUILDING_DLL BUILDING_DIRECT_MOTIONTRAIL

  #define OTHER_LIBS \
    linmath:c \
    mathutil:c \
    gobj:c \
    putil:c \
    pipeline:c \
    event:c \
    pstatclient:c \
    pnmimage:c \
    $[if $[HAVE_NET],net:c] $[if $[WANT_NATIVE_NET],nativenet:c] \
    pgraph:c \
    panda:m \
    express:c \
    downloader:c \
    pandaexpress:m \
    interrogatedb \
    \
     \
    dtoolutil:c \
    dtoolbase:c \
    dtool:m \
    pandabase:c \
    prc \
    gsgbase:c \
    parametrics:c


  #define SOURCES \
    config_motiontrail.cxx config_motiontrail.h \
    cMotionTrail.cxx cMotionTrail.h

  #define INSTALL_HEADERS \
    config_motiontrail.h \
    cMotionTrail.h

  #define IGATESCAN all
#end lib_target
