#define C++FLAGS -DWITHIN_PANDA

#begin lib_target
  #define TARGET directbase
  #define USE_PACKAGES eigen sleef
  #if $[HAVE_PYTHON]
    #define USE_PACKAGES $[USE_PACKAGES] python
  #endif
  
  #define BUILDING_DLL BUILDING_DIRECT_DIRECTBASE

  #define OTHER_LIBS dtoolbase:c dtool:m panda:m express:c pandaexpress:m interrogatedb

  #define SOURCES \
    directbase.h directsymbols.h \
    pythonPointerTo.I pythonPointerTo.h
    
  #define COMPOSITE_SOURCES  \
    pythonPointerTo.cxx

  #define INSTALL_HEADERS \
    directbase.h directsymbols.h \ 
    pythonPointerTo.I pythonPointerTo.h
    
  #define IGATESCAN all

  // These libraries and frameworks are used by dtoolutil; we redefine
  // them here so they get into the panda build system.
  #if $[ne $[PLATFORM], FreeBSD]
    #define UNIX_SYS_LIBS dl
  #endif
  #define WIN_SYS_LIBS shell32.lib
  #define OSX_SYS_FRAMEWORKS Foundation $[if $[not $[BUILD_IPHONE]],AppKit]

#end lib_target
