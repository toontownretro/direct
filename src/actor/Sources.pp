#define C++FLAGS -DWITHIN_PANDA

#begin lib_target
  #define BUILD_TARGET $[HAVE_PYTHON]
  #define USE_PACKAGES openssl native_net net

  #define BUILDING_DLL BUILDING_DIRECT_ACTOR

  #define TARGET actor
  #define LOCAL_LIBS \
    directbase dcparser
  #define OTHER_LIBS \
    anim:c event:c downloader:c panda:m pandaegg:m express:c pandaexpress:m pgraph:c pgraphnodes:c \
    interrogatedb  \
    dtoolutil:c dtoolbase:c dtool:m \
    prc pstatclient:c linmath:c putil:c \
    pipeline:c $[if $[HAVE_NET],net:c] $[if $[WANT_NATIVE_NET],nativenet:c]

  #define SOURCES \
    config_actor.cxx config_actor.h \
    cActor.cxx cActor.I cActor.h

  #define IGATESCAN all

#end lib_target
