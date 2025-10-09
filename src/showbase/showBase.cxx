/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file showBase.cxx
 * @author shochet
 * @date 2000-02-02
 */

#ifdef __APPLE__
// We have to include this before we include any Panda libraries, because one
// of the things we pick up in Panda defines a macro for TCP_NODELAY and
// friends, causing heartaches for the header files picked up here.
#include <Carbon/Carbon.h>
extern "C" { void CPSEnableForegroundOperation(ProcessSerialNumber* psn); }
#endif

#include "showBase.h"
#include "graphicsWindow.h"
#include "renderBuffer.h"
#include "camera.h"
#include "characterNode.h"
#include "graphicsPipeSelection.h"
#include "jobSystem.h"

#ifdef _WIN32
#include <windows.h>  // For SystemParametersInfo()
STICKYKEYS g_StartupStickyKeys = {sizeof(STICKYKEYS), 0};
TOGGLEKEYS g_StartupToggleKeys = {sizeof(TOGGLEKEYS), 0};
FILTERKEYS g_StartupFilterKeys = {sizeof(FILTERKEYS), 0};
#endif

using std::max;
using std::min;

#if !defined(CPPPARSER) && !defined(LINK_ALL_STATIC) && !defined(BUILDING_DIRECT_SHOWBASE)
  #error Buildsystem error: BUILDING_DIRECT_SHOWBASE not defined
#endif

ConfigureDef(config_showbase);
ConfigureFn(config_showbase) {
}

ConfigVariableSearchPath particle_path
("particle-path",
 PRC_DESC("The directories to search for particle files to be loaded."));
 
ConfigVariableBool parallel_animation
("parallel-animation", false,
 PRC_DESC("When cull-animation is false, this controls whether or not "
          "animations for all characters should be computed in parallel."));
          
TypeHandle CShowBase::_type_handle;

ConfigVariableSearchPath &
get_particle_path() {
  return particle_path;
}

AsyncTask::DoneStatus CShowBase::
traverse_collisions(GenericAsyncTask *task, void *user_data) {
  CShowBase *this_ptr = (CShowBase *)user_data;
  
  if (!this_ptr->traversal_path || this_ptr->traversal_path.is_empty()) { return AsyncTask::DoneStatus::DS_cont; }
  
  JobSystem *js = JobSystem::get_global_ptr();
  js->parallel_process(this_ptr->traversers.size(), [&] (int i) {
  //for (size_t i = 0; i < this_ptr->traversers.size(); ++i) {
    CollisionTraverser *traverser = this_ptr->traversers[i];
    traverser->traverse(this_ptr->traversal_path);
  //};
  }, 2);
  
  throw_event("collisionLoopFinished");
  return AsyncTask::DoneStatus::DS_cont;
}

void CShowBase::
add_collision_traverser(CollisionTraverser *trav) {
  nassertv(trav != nullptr);
  traversers.push_back(trav);
}

void CShowBase::
begin_collisions_traversal(PT(AsyncTaskManager) mgr, NodePath &path) {
  if (!mgr || !path || collision_task) { return; }
  
  // This is the NodePath we will traverse with.
  traversal_path = path;
  
  // Create our task to traverse collisions.
  collision_task = new GenericAsyncTask("collisionLoop", &traverse_collisions, this);
  // Make the collisionLoop task run before igLoop,
  // but leave enough room for the app to insert tasks
  // between collisionLoop and igLoop
  collision_task->set_sort(30);
  // Add the task to the task manager.
  mgr->add(collision_task);
}

void CShowBase::
stop_collisions_traversal() {
  // Remove our collisions task.
  if (collision_task) {
      collision_task->remove();
      delete collision_task;
  }
  collision_task = nullptr;
    
  // Clear all of our traversers.
  traversers.clear();
}

void CShowBase::
anim_traverse_single(PandaNode *node) {
  // Visit all the children.
  PandaNode::Children children = node->get_children();
  int num_children = children.get_num_children();
  for (int i = 0; i < num_children; ++i) {
    const PandaNode::DownConnection &child = children.get_child_connection(i);
    anim_traverse_single(child.get_child());
  }
  
  // If we aren't dealing with a character, Then just return,
  if (!node->is_of_type(CharacterNode::get_class_type())) { return; }
  
  CharacterNode *char_node = (CharacterNode *)node;
  char_node->update(false);
}

void CShowBase::
anim_traverse_parallel(PandaNode *node) {
  // Visit all the children.
  PandaNode::Children children = node->get_children();
  JobSystem *js = JobSystem::get_global_ptr();
  js->parallel_process_per_item(children.get_num_children(), [this, &children] (int i) {
    const PandaNode::DownConnection &child = children.get_child_connection(i);
    anim_traverse_parallel(child.get_child());
  });
  
  // If we aren't dealing with a character, Then just return,
  if (!node->is_of_type(CharacterNode::get_class_type())) { return; }
  
  CharacterNode *char_node = (CharacterNode *)node;
  char_node->update(false);
}

AsyncTask::DoneStatus CShowBase::
animate_characters(GenericAsyncTask *task, void *user_data) {
  CShowBase *this_ptr = (CShowBase *)user_data;
  
  if (!this_ptr->root_node ) { return AsyncTask::DoneStatus::DS_cont; }
  
  if (parallel_animation) {
    this_ptr->anim_traverse_parallel(this_ptr->root_node);
  } else {
    this_ptr->anim_traverse_single(this_ptr->root_node);
  }
  
  return AsyncTask::DoneStatus::DS_cont;
}

void CShowBase::
begin_animate_characters(PT(AsyncTaskManager) mgr, NodePath &root) {
  if (!mgr || animate_task) { return; }
  
  if (root.is_empty()) { return; }
    
  // This is the root NodePath all of the characters we will animate are children of.
  root_node = root.node();
  
  // Create our task to animate characters.
  animate_task = new GenericAsyncTask("animateCharacters", &animate_characters, this);
  // We will animate AFTER collisions are handled.
  animate_task->set_sort(31);
  // Add the task to the task manager.
  mgr->add(animate_task);
}

void CShowBase::
stop_animate_characters() {
  // Remove our collisions task.
  if (animate_task) {
      animate_task->remove();
      delete animate_task;
  }
  animate_task = nullptr;
  
  // We no longer reference the old path.
  root_node = nullptr;
}

void CShowBase::
start_ig_loop(PT(AsyncTaskManager) mgr, int sort) {
  if (!mgr || ig_loop_task) { return; }
  
  // Create our task to handle rendering and some other things.
  ig_loop_task = new GenericAsyncTask("igLoop", &ig_loop, this);
  // We allow a custom sort if needed.
  ig_loop_task->set_sort(sort);
  // Add the task to the task manager.
  mgr->add(ig_loop_task);
}

void CShowBase::
stop_ig_loop() {
  if (ig_loop_task) {
      ig_loop_task->remove();
      delete ig_loop_task;
  }
  ig_loop_task = nullptr;
}

AsyncTask::DoneStatus CShowBase::
ig_loop(GenericAsyncTask *task, void *user_data) {
  CShowBase *this_ptr = (CShowBase *)user_data;
  PT(GraphicsEngine) engine = this_ptr->get_graphics_engine();
  
  // TODO: Support OnScreenDebug.
  
  // TODO: Support Recorder.
  
  // Finally, render the frame.
  engine->render_frame();
  if (this_ptr->cluster_sync_flag) {
    engine->sync_frame();
  }
  
  this_ptr->throw_new_frame();
  return AsyncTask::DoneStatus::DS_cont;
}

// Initialize the application for making a Gui-based app, such as wx.  At the
// moment, this is a no-op except on Mac.
void
init_app_for_gui() {
#ifdef IS_OSX
  // Rudely bring the application to the foreground.  This is particularly
  // important when running wx via the plugin, since the plugin app is seen as
  // separate from the browser app, even though the user sees them as the same
  // thing.  We need to bring the plugin app to the foreground to make its wx
  // windows visible.
  activate_osx_application();
#endif

  // We don't appear need to do the following, however, if we launch the
  // plugin correctly from its own bundle.
  /*
  static bool initted_for_gui = false;
  if (!initted_for_gui) {
    initted_for_gui = true;
#ifdef IS_OSX
    ProcessSerialNumber psn;

    GetCurrentProcess(&psn);
    CPSEnableForegroundOperation(&psn);
    SetFrontProcess(&psn);
#endif  // IS_OSX
  }
  */
}

void
store_accessibility_shortcut_keys() {
#ifdef _WIN32
  SystemParametersInfo(SPI_GETSTICKYKEYS, sizeof(STICKYKEYS), &g_StartupStickyKeys, 0);
  SystemParametersInfo(SPI_GETTOGGLEKEYS, sizeof(TOGGLEKEYS), &g_StartupToggleKeys, 0);
  SystemParametersInfo(SPI_GETFILTERKEYS, sizeof(FILTERKEYS), &g_StartupFilterKeys, 0);
#endif
}

void
allow_accessibility_shortcut_keys(bool allowKeys) {
#ifdef _WIN32
  if( allowKeys )
  {
    // Restore StickyKeysetc to original state and enable Windows key
    SystemParametersInfo(SPI_SETSTICKYKEYS, sizeof(STICKYKEYS), &g_StartupStickyKeys, 0);
    SystemParametersInfo(SPI_SETTOGGLEKEYS, sizeof(TOGGLEKEYS), &g_StartupToggleKeys, 0);
    SystemParametersInfo(SPI_SETFILTERKEYS, sizeof(FILTERKEYS), &g_StartupFilterKeys, 0);
  } else {
    // Disable StickyKeysetc shortcuts but if the accessibility feature is on,
    // then leave the settings alone as its probably being usefully used

    STICKYKEYS skOff = g_StartupStickyKeys;
    if( (skOff.dwFlags & SKF_STICKYKEYSON) == 0 )
    {
      // Disable the hotkey and the confirmation
      skOff.dwFlags &= ~SKF_HOTKEYACTIVE;
      skOff.dwFlags &= ~SKF_CONFIRMHOTKEY;

      SystemParametersInfo(SPI_SETSTICKYKEYS, sizeof(STICKYKEYS), &skOff, 0);
    }

    TOGGLEKEYS tkOff = g_StartupToggleKeys;
    if( (tkOff.dwFlags & TKF_TOGGLEKEYSON) == 0 )
    {
      // Disable the hotkey and the confirmation
      tkOff.dwFlags &= ~TKF_HOTKEYACTIVE;
      tkOff.dwFlags &= ~TKF_CONFIRMHOTKEY;

      SystemParametersInfo(SPI_SETTOGGLEKEYS, sizeof(TOGGLEKEYS), &tkOff, 0);
    }

    FILTERKEYS fkOff = g_StartupFilterKeys;
    if( (fkOff.dwFlags & FKF_FILTERKEYSON) == 0 )
    {
      // Disable the hotkey and the confirmation
      fkOff.dwFlags &= ~FKF_HOTKEYACTIVE;
      fkOff.dwFlags &= ~FKF_CONFIRMHOTKEY;

      SystemParametersInfo(SPI_SETFILTERKEYS, sizeof(FILTERKEYS), &fkOff, 0);
    }
  }
#endif
}

#if 0
int TempGridZoneManager::
add_grid_zone(unsigned int x,
              unsigned int y,
              unsigned int width,
              unsigned int height,
              unsigned int zoneBase,
              unsigned int xZoneResolution,
              unsigned int yZoneResolution) {
  // zoneBase is the first zone in the grid (e.g.  the upper left)
  // zoneResolution is the number of cells on each axsis.  returns the next
  // available zoneBase (i.e.  zoneBase+xZoneResolution*yZoneResolution)
  std::cerr<<"adding grid zone with a zoneBase of "<<zoneBase<<" and a zoneResolution of "<<zoneResolution;
  _grids.append(TempGridZoneManager::GridZone(x, y, width, height, zoneBase, xZoneResolution, yZoneResolution));
  return zoneBase+xZoneResolution*yZoneResolution;
}

void TempGridZoneManager::GridZone
GridZone(unsigned int x,
         unsigned int y,
         unsigned int width,
         unsigned int height,
         unsigned int zoneBase,
         unsigned int xZoneResolution,
         unsigned int yZoneResolution) {
  _x=x;
  _y=y;
  _width=width;
  _height=heigth;
  _zoneBase=zoneBase;
  _xZoneResolution=xZoneResolution;
  _yZoneResolution=yZoneResolution;

  // The cellVis is the number of cells radius that can be seen, including the
  // center cell.  So, for a 5 x 5 visible area, the cellVis is 3.
  const float cellVis=3.0;
  unsigned int xMargine=(unsigned int)((float)width/(float)xZoneResolution*cellVis+0.5);
  unsigned int yMargine=(unsigned int)((float)height/(float)yZoneResolution*cellVis+0.5);
  _xMinVis=x-xMargine;
  _yMinVis=y-yMargine;
  _xMaxVis=x+width+xMargine;
  _yMaxVis=y+height+yMargine;
}

void TempGridZoneManager::
get_grids(int x, int y) {
  TempGridZoneManager::ZoneSet canSee;
  TempGridZoneManager::GridSet::const_iterator i=_grids.begin();
  for (; i!=_grids.end(); ++i) {
    if (x >= i._xMinVis && x < i._xMaxVis && y >= i._yMinVis && y < i._yMaxVis) {
      add_to_zone_list(i, x, y, canSee);
    }
  }
}

void TempGridZoneManager::
add_to_zone_list(const TempGridZoneManager::GridZone &gridZone,
    unsigned int x,
    unsigned int y,
    TempGridZoneManager::ZoneSet &zoneSet) {
  unsigned int xRes=gridZone._xZoneResolution;
  unsigned int yRes=gridZone._yZoneResolution;
  float xP=((float)(x-gridZone._x))/gridZone._width;
  float yP=((float)(y-gridZone._y))/gridZone._height;
  int xCell=(int)(xP*xRes);
  int yCell=(int)(yP*yRes);

  // range is how many cells can be seen in each direction:
  const int range=2;
  int yBegin=max(0, yCell-range);
  int yEnd=min(yRes, yCell+range);
  int xBegin=max(0, xCell-range);
  int xEnd=min(xRes, xCell+range);
  unsigned int zone=gridZone._zoneBase+yBegin*xRes+xBegin;

  for (yCell=yBegin; yCell < yEnd; ++yCell) {
    for (xCell=xBegin; xCell < xEnd; ++xCell) {
      zoneSet.append(zone+xCell);
    }
    zone+=xRes;
  }
}

int TempGridZoneManager::
get_zone_list(int x, int y, int resolution) {
  // x is a float in the range 0.0 to 1.0 y is a float in the range 0.0 to 1.0
  // resolution is the number of cells on each axsis.  returns a list of zone
  // ids.  Create a box of cell numbers, while clipping to the edges of the
  // set of cells.
  if (x < 0.0 || x > 1.0 || y < 0.0 || y > 1.0) {
    return 0;
  }
  std::cerr<<"resolution="<<resolution;
  xCell=min(int(x*resolution), resolution-1)
  yCell=min(int(y*resolution), resolution-1)
  cell=yCell*resolution+xCell
  print "cell", cell,
  zone=zoneBase+cell
  print "zone", zone

  zone=zone-2*resolution
  endZone=zone+5*resolution
  yCell=yCell-2
  while zone < endZone:
      if yCell >= 0 and yCell < resolution:
          if xCell > 1:
              zoneList.append(zone-2)
              zoneList.append(zone-1)
          elif xCell > 0:
              zoneList.append(zone-1)
          r.append(zone)
          if xCell < resolution-2:
              zoneList.append(zone+1)
              zoneList.append(zone+2)
          elif xCell < resolution-1:
              zoneList.append(zone+1)
      yCell+=1
      zone+=resolution
  return zoneList
  return 5;
}
#endif
