#begin lib_target
  #define TARGET showbase
  #define LOCAL_LIBS \
    directbase
  #define OTHER_LIBS \
    pgraph:c pgraphnodes:c gsgbase:c gobj:c mathutil:c pstatclient:c \
    downloader:c pandabase:c pnmimage:c prc \
    pipeline:c cull:c \
    $[if $[HAVE_NET],net:c] $[if $[WANT_NATIVE_NET],nativenet:c] \
    display:c linmath:c event:c putil:c panda:m \
    express:c pandaexpress:m \
    interrogatedb  \
    dtoolutil:c dtoolbase:c dtool:m

  #define BUILDING_DLL BUILDING_DIRECT_SHOWBASE

  #define WIN_SYS_LIBS \
    User32.lib

  #define SOURCES \
    showBase.cxx showBase.h \
    $[if $[IS_OSX],showBase_assist.mm]

  #define IGATESCAN all
#end lib_target

// Define a Python extension module for operating on frozen modules.
// This is a pure C module; it involves no Panda code or C++ code.
#begin python_target
  #define TARGET panda3d.extend_frozen
  #define SOURCES extend_frozen.c
#end python_target
