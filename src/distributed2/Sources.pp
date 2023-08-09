#define C++FLAGS -DWITHIN_PANDA

#define BUILD_DIRECTORY $[HAVE_DISTRIBUTED2]

#begin lib_target
  #define TARGET distributed2

  #define LOCAL_LIBS \
    directbase dcparser

  #define OTHER_LIBS \
    linmath:c mathutil:c

  #define BUILDING_DLL BUILDING_DIRECT_DISTRIBUTED2

  #define SOURCES \
    config_distributed2.h config_distributed2.N \
    changeFrameList.h changeFrameList.I \
    clientAnimLayer.h clientAnimLayer.I \
    clientFrame.h clientFrame.I \
    clientFrameManager.h clientFrameManager.I \
    frameSnapshot.h frameSnapshot.I \
    frameSnapshotEntry.h frameSnapshotEntry.I \
    packedObject.h packedObject.I

  #define COMPOSITE_SOURCES \
    config_distributed2.cxx \
    changeFrameList.cxx \
    clientAnimLayer.cxx \
    clientFrame.cxx \
    clientFrameManager.cxx \
    frameSnapshot.cxx \
    frameSnapshotEntry.cxx \
    packedObject.cxx

  #define IGATESCAN all

  #define IGATEEXT \
    cClientRepository.cxx \
    cClientRepository.h cClientRepository.I \
    frameSnapshotManager.h frameSnapshotManager.I frameSnapshotManager.cxx

#end lib_target
