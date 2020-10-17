#define C++FLAGS -DWITHIN_PANDA

#begin lib_target
  #define TARGET distributed2

  #define LOCAL_LIBS \
    directbase dcparser

  //#define OTHER_LIBS \

  #define BUILDING_DLL BUILDING_DIRECT_DISTRIBUTED2

  #define SOURCES \
    config_distributed2.h \
    changeFrameList.h changeFrameList.I \
    clientFrame.h clientFrame.I \
    clientFrameManager.h clientFrameManager.I \
    frameSnapshot.h frameSnapshot.I \
    frameSnapshotEntry.h frameSnapshotEntry.I \
    frameSnapshotManager.h frameSnapshotManager.I \
    packedObject.h packedObject.I

  #define COMPOSITE_SOURCES \
    config_distributed2.cxx \
    changeFrameList.cxx \
    clientFrame.cxx \
    clientFrameManager.cxx \
    frameSnapshot.cxx \
    frameSnapshotEntry.cxx \
    frameSnapshotManager.cxx \
    packedObject.cxx

  #define IGATESCAN all

  #define IGATEEXT \
    cClientRepository.cxx \
    cClientRepository.h cClientRepository.I \
    frameSnapshotManager_ext.cxx \
    frameSnapshotManager_ext.h

#end lib_target
