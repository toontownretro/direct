#define LOCAL_LIBS \
  directbase

#define OTHER_LIBS \
  dtool:m \
  dtoolbase:c dtoolutil:c \
  prc \
  panda:m \
  pgraph:c gobj:c putil:c mathutil:c linmath:c express:c

#begin lib_target
  #define TARGET foundry

  #define BUILDING_DLL BUILDING_DIRECT_FOUNDRY

  #define SOURCES \
    config_foundry.h \
    planeCulledGeomNode.h \
    solidGeomNode.h

  #define COMPOSITE_SOURCES \
    config_foundry.cxx \
    planeCulledGeomNode.cxx \
    solidGeomNode.cxx

  #define IGATESCAN all

#end lib_target
