#define LOCAL_LIBS \
  dcparser
#define OTHER_LIBS \
  express:c pandaexpress:m \
  interrogatedb  \
  dtoolutil:c dtoolbase:c dtool:m \
  prc pstatclient:c linmath:c putil:c \
  pipeline:c downloader:c \
  $[if $[HAVE_NET],net:c] $[if $[WANT_NATIVE_NET],nativenet:c] \
  panda:m

#begin bin_target
  #define TARGET dcparse
  #define USE_PACKAGES zlib openssl

  #define C++FLAGS $[C++FLAGS] -DWITHIN_PANDA

  #define SOURCES \
    dcparse.cxx
  #define WIN_SYS_LIBS shell32.lib
#end bin_target
