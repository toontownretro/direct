#define BUILD_DIRECTORY $[WANT_NATIVE_NET]
#define USE_PACKAGES native_net

#define OTHER_LIBS \
    express:c pandaexpress:m \
    pstatclient:c pipeline:c panda:m \
    interrogatedb \
    dtoolutil:c dtoolbase:c dtool:m prc \
    $[if $[HAVE_NET],net:c] $[if $[WANT_NATIVE_NET],nativenet:c] \
    linmath:c putil:c

#define LOCAL_LIBS \
    directbase
#define C++FLAGS -DWITHIN_PANDA
#define UNIX_SYS_LIBS m
#define USE_PACKAGES python

#begin lib_target
  #define TARGET  http

  #define COMPOSITE_SOURCES \
     config_http.cxx \
     http_connection.cxx \
     parsedhttprequest.cxx \
     http_request.cxx

  #define SOURCES \
     config_http.h \
     application_log.h \
     baseincomingset.h baseincomingset.i \
     bufferedwriter_growable.h \
     http_bufferedreader.h http_bufferedreader.i \
     http_connection.h  \
     http_request.h \
     parsedhttprequest.h \
     ringbuffer_slide.h ringbuffer_slide.i \
     strtargetbuffer.h

  #define BUILDING_DLL BUILDING_DIRECT_HTTP

  #define WIN_SYS_LIBS Ws2_32.lib

  #define IGATESCAN all
#end lib_target
