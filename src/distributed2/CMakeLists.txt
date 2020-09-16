if(NOT HAVE_PYTHON)
  return()
endif()

set(P3DISTRIBUTED2_HEADERS
  config_distributed2.h
  cClientRepository.h
  cClientRepository.I
  changeFrameList.h
  changeFrameList.I
  clientFrame.h
  clientFrame.I
  clientFrameManager.h
  clientFrameManager.I
  frameSnapshot.h
  frameSnapshot.I
  frameSnapshotEntry.h
  frameSnapshotEntry.I
  frameSnapshotManager.h
  frameSnapshotManager.I
  packedObject.h
  packedObject.I
)

set(P3DISTRIBUTED2_SOURCES
  config_distributed2.cxx
  changeFrameList.cxx
  clientFrame.cxx
  clientFrameManager.cxx
  frameSnapshot.cxx
  frameSnapshotEntry.cxx
  frameSnapshotManager.cxx
  packedObject.cxx
)

set(P3DISTRIBUTED2_IGATEEXT
  cClientRepository.cxx
  frameSnapshotManager_ext.cxx
  frameSnapshotManager_ext.h
)

add_component_library(p3distributed2 NOINIT SYMBOL BUILDING_DIRECT_DISTRIBUTED2
  ${P3DISTRIBUTED2_HEADERS} ${P3DISTRIBUTED2_SOURCES})
target_link_libraries(p3distributed2 p3directbase p3dcparser panda)
target_interrogate(p3distributed2 ${P3DISTRIBUTED2_HEADERS} ${P3DISTRIBUTED2_SOURCES} EXTENSIONS ${P3DISTRIBUTED2_IGATEEXT})

if(NOT BUILD_METALIBS)
  install(TARGETS p3distributed2
    EXPORT Direct COMPONENT Direct
    DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
    INCLUDES DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/panda3d
    ARCHIVE COMPONENT DirectDevel)
endif()
install(FILES ${P3DISTRIBUTED2_HEADERS} COMPONENT DirectDevel DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/panda3d)
