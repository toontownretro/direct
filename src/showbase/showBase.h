/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file showBase.h
 * @author shochet
 * @date 2000-02-02
 */

#ifndef SHOWBASE_H
#define SHOWBASE_H

#include "directbase.h"

//#include "animControl.h"
#include "asyncTaskManager.h"
#include "configVariableBool.h"
#include "configVariableSearchPath.h"
#include "collisionTraverser.h"
#include "dconfig.h"
#include "dSearchPath.h"
#include "eventHandler.h"
#include "genericAsyncTask.h"
#include "graphicsEngine.h"
#include "graphicsWindow.h"
#include "graphicsPipe.h"
#include "nodePath.h"
#include "pointerTo.h"
#include "throw_event.h"

ConfigureDecl(config_showbase, EXPCL_DIRECT_SHOWBASE, EXPTP_DIRECT_SHOWBASE);

class CollisionTraverser;
class Camera;
class GraphicsEngine;

class EXPCL_DIRECT_SHOWBASE CShowBase : public TypedWritableReferenceCount {
PUBLISHED:
  INLINE CShowBase();
  INLINE ~CShowBase();

  void add_collision_traverser(CollisionTraverser *trav);
  void begin_collisions_traversal(PT(AsyncTaskManager) mgr, NodePath &path);
  void stop_collisions_traversal();

  void begin_animate_characters(PT(AsyncTaskManager) mgr, NodePath &root);
  void stop_animate_characters();
  
  void start_ig_loop(PT(AsyncTaskManager) mgr, int sort=50);
  void stop_ig_loop();
  
  INLINE PT(GraphicsEngine) get_graphics_engine();
  
  INLINE void throw_new_frame();

private:
  static AsyncTask::DoneStatus traverse_collisions(GenericAsyncTask *task, void *user_data);
  
  void anim_traverse_single(PandaNode *node);
  void anim_traverse_parallel(PandaNode *node);
  static AsyncTask::DoneStatus animate_characters(GenericAsyncTask *task, void *user_data);
  
  static AsyncTask::DoneStatus ig_loop(GenericAsyncTask *task, void *user_data);
  
PUBLISHED:
  bool cluster_sync_flag = false;
  bool multi_client_sleep = false;
  bool main_win_minimized = false;
  
private:
  // Collision Traversal
  NodePath traversal_path;
  PT(GenericAsyncTask) collision_task = nullptr;
  pvector<CollisionTraverser *> traversers;

  // Character Animation
  PT(PandaNode) root_node = nullptr;
  PT(GenericAsyncTask) animate_task = nullptr;
  
  // Frame Rendering
  PT(GraphicsEngine) graphics_engine = nullptr;
  PT(GenericAsyncTask) ig_loop_task = nullptr;

public:
  virtual TypeHandle get_type() const {
    return get_class_type();
  }
  virtual TypeHandle force_init_type() {init_type(); return get_class_type();}
  static TypeHandle get_class_type() {
    return _type_handle;
  }
  static void init_type() {
    TypedWritableReferenceCount::init_type();
    register_type(_type_handle, "CShowBase",
                  TypedWritableReferenceCount::get_class_type());
  }

private:
  static TypeHandle _type_handle;
};

BEGIN_PUBLISH

EXPCL_DIRECT_SHOWBASE ConfigVariableSearchPath &get_particle_path();

EXPCL_DIRECT_SHOWBASE void init_app_for_gui();

// to handle windows stickykeys
EXPCL_DIRECT_SHOWBASE void store_accessibility_shortcut_keys();
EXPCL_DIRECT_SHOWBASE void allow_accessibility_shortcut_keys(bool allowKeys);

#ifdef IS_OSX
EXPCL_DIRECT_SHOWBASE void activate_osx_application();
#endif

END_PUBLISH


#if 0
class TempGridZoneManager {
PUBLISHED:
  TempGridZoneManager() {}
  ~TempGridZoneManager() {}

  unsigned int add_grid_zone(
      unsigned int x,
      unsigned int y,
      unsigned int width,
      unsigned int height,
      unsigned int zoneBase,
      unsigned int xZoneResolution,
      unsigned int yZoneResolution);
  int get_zone_list(int x, int y);

protected:
  class GridZone {
  public:
    unsigned int base;
    unsigned int resolution;
    GridZone(
        unsigned int x,
        unsigned int y,
        unsigned int width,
        unsigned int height,
        unsigned int zoneBase,
        unsigned int xZoneResolution,
        unsigned int yZoneResolution) {
      base=zoneBase;
      resolution=zoneResolution;
    }
  };
  Set<GridZone> _grids;
};
#endif

#include "showBase.I"

#endif
