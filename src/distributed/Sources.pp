#define C++FLAGS -DWITHIN_PANDA

#begin lib_target
  #define BUILD_TARGET $[HAVE_PYTHON]
  #define USE_PACKAGES openssl native_net net

  #define BUILDING_DLL BUILDING_DIRECT_DISTRIBUTED

  #define TARGET distributed
  #define LOCAL_LIBS \
    directbase dcparser
  #define OTHER_LIBS \
    event:c downloader:c panda:m express:c pandaexpress:m \
    interrogatedb  \
    dtoolutil:c dtoolbase:c dtool:m \
    prc pstatclient:c pandabase:c linmath:c putil:c \
    pipeline:c $[if $[HAVE_NET],net:c] $[if $[WANT_NATIVE_NET],nativenet:c]

  #define SOURCES \
    config_distributed.cxx config_distributed.h \
    cConnectionRepository.I \
    cConnectionRepository.h \
    cDistributedSmoothNodeBase.I \
    cDistributedSmoothNodeBase.h

  #define IGATESCAN all

  #define IGATEEXT \
    cConnectionRepository.cxx \
    cDistributedSmoothNodeBase.cxx

#end lib_target
