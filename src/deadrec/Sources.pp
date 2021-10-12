#begin lib_target
  #define TARGET deadrec
  #define LOCAL_LIBS \
    directbase
  #define OTHER_LIBS \
    express:c linmath:c \
    interrogatedb \
    dtoolutil:c dtoolbase:c dtool:m \
    prc pandabase:c putil:c \
    pipeline:c pgraph:c panda:m

  #define BUILDING_DLL BUILDING_DIRECT_DEADREC

  #define SOURCES \
    config_deadrec.h \
    smoothMover.h smoothMover.I

  #define COMPOSITE_SOURCES \
    config_deadrec.cxx \
    smoothMover.cxx

  #define INSTALL_HEADERS \
    config_deadrec.h \
    smoothMover.h smoothMover.I

  #define IGATESCAN \
    all
#end lib_target
