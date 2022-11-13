#begin python_module_target
  #define C++FLAGS -DWITHIN_PANDA
  #define TARGET panda3d.direct
  #define IGATE_LIBS \
    actor dcparser deadrec interval motiontrail showbase \
    distributed distributed2 foundry
  #define IMPORT panda3d.core
  #define LOCAL_LIBS direct
#end python_module_target
