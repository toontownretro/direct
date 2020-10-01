#begin python_module_target
  #define C++FLAGS -DWITHIN_PANDA
  #define TARGET panda3d.direct
  #define IGATE_LIBS \
    p3dcparser p3deadrec p3interval p3motiontrail p3showbase \
    p3distributed
  #define IMPORT panda3d.core
  #define LOCAL_LIBS p3direct
#end python_module_target
