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

  //#define COMBINED_SOURCES $[TARGET]_composite1.cxx  

  #define COMPOSITE_SOURCES \
     config_http.cxx \
     http_connection.cxx \
     parsedhttprequest.cxx \
     http_request.cxx

  #define SOURCES \
     config_http.h \
     http_connection.h  \
     http_request.h

  #define BUILDING_DLL BUILDING_DIRECT_HTTP


  #define IGATESCAN all
#end lib_target
