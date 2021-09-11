#begin lib_target
  #define TARGET interval
  #define LOCAL_LIBS \
    directbase
  #define OTHER_LIBS \
    downloader:c linmath:c \
    anim:c event:c gobj:c pnmimage:c mathutil:c \
    pgraph:c putil:c panda:m express:c pandaexpress:m \
    interrogatedb  \
    dtoolutil:c dtoolbase:c dtool:m \
    pandabase:c prc gsgbase:c pstatclient:c \
    $[if $[HAVE_NET],net:c] $[if $[WANT_NATIVE_NET],nativenet:c] \
    pipeline:c

  #define BUILDING_DLL BUILDING_DIRECT_INTERVAL

  #define SOURCES \
    config_interval.cxx config_interval.h \
    cInterval.cxx cInterval.I cInterval.h \
    cIntervalManager.cxx cIntervalManager.I cIntervalManager.h \
    cConstraintInterval.cxx cConstraintInterval.I cConstraintInterval.h \
    cConstrainTransformInterval.cxx cConstrainTransformInterval.I cConstrainTransformInterval.h \
    cConstrainPosInterval.cxx cConstrainPosInterval.I cConstrainPosInterval.h \
    cConstrainHprInterval.cxx cConstrainHprInterval.I cConstrainHprInterval.h \
    cConstrainPosHprInterval.cxx cConstrainPosHprInterval.I cConstrainPosHprInterval.h \
    cLerpInterval.cxx cLerpInterval.I cLerpInterval.h \
    cLerpNodePathInterval.cxx cLerpNodePathInterval.I cLerpNodePathInterval.h \
    //cLerpAnimEffectInterval.cxx cLerpAnimEffectInterval.I cLerpAnimEffectInterval.h \
    cMetaInterval.cxx cMetaInterval.I cMetaInterval.h \
    hideInterval.cxx hideInterval.I hideInterval.h \
    lerpblend.cxx lerpblend.h \
    showInterval.cxx showInterval.I showInterval.h \
    waitInterval.cxx waitInterval.I waitInterval.h \
    lerp_helpers.h

  #define INSTALL_HEADERS \
    config_interval.h \
    cInterval.I cInterval.h \
    cIntervalManager.I cIntervalManager.h \
    cConstraintInterval.I cConstraintInterval.h \
    cConstrainTransformInterval.I cConstrainTransformInterval.h \
    cConstrainPosInterval.I cConstrainPosInterval.h \
    cConstrainHprInterval.I cConstrainHprInterval.h \
    cConstrainPosHprInterval.I cConstrainPosHprInterval.h \
    cLerpInterval.I cLerpInterval.h \
    cLerpNodePathInterval.I cLerpNodePathInterval.h \
    //cLerpAnimEffectInterval.I cLerpAnimEffectInterval.h \
    cMetaInterval.I cMetaInterval.h \
    hideInterval.I hideInterval.h \
    lerpblend.h \
    showInterval.I showInterval.h \
    waitInterval.I waitInterval.h \
    lerp_helpers.h

  #define IGATESCAN all
  #define IGATEEXT \
    cInterval_ext.h cInterval_ext.cxx

#end lib_target
