/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file messenger.h
 * @author Prince Frizzy
 * @date 2023-09-16
 */

#ifndef MESSENGER_H
#define MESSENGER_H

#include "directbase.h"

// This is only ever actually needed if we compile for Python.
#ifdef HAVE_PYTHON

#include <sstream> 

#include "asyncTask.h"
#include "asyncTaskManager.h"
#include "eventHandler.h"
#include "pointerTo.h"
#include "pythonPointerTo.h"
#include "reMutex.h"
#include "reMutexHolder.h"
#include "string_utils.h"
#include "throw_event.h"
#include "typedReferenceCount.h"

#include "py_panda.h"

class Messenger;
class MessengerChainTask;

class EXPCL_DIRECT_SHOWBASE Messenger : public TypedReferenceCount {
PUBLISHED:
  Messenger();
  ~Messenger();
  
  PyObject *get_messenger_id(PYPT object);
  void store_object(PYPT object);
  PyObject *get_object(PYPT id);
  PyObject *get_objects();
  Py_ssize_t get_num_listeners(PYPT event);
  PyObject *get_events();
  void release_object(PYPT object);
  
  PyObject *future(PYPT event);
  
  INLINE void accept(PYPT event, PYPT object, PYPT method);
  INLINE void accept(PYPT event, PYPT object, PYPT method, PYPT extra_args);
  void accept(PYPT event, PYPT object, PYPT method, PYPT extra_args, bool persistent);
  
  void ignore(PYPT event, PYPT object);
  void ignore_all(PYPT object);
  PyObject *get_all_accepting(PYPT object);
  bool is_accepting(PYPT event, PYPT object);
  bool is_ignoring(PYPT event, PYPT object);
  PyObject *who_accepts(PYPT event);
  
  INLINE void send(PYPT event);
  INLINE void send(PYPT event, PYPT sent_args);
  void send(PYPT event, PYPT sent_args, PYPT task_chain);
  
  void clear();
  
  bool is_empty();
  
  INLINE static Messenger *get_global_ptr();
  
private:
  static AsyncTask::DoneStatus task_chain_dispatch(MessengerChainTask *task, PT(Messenger) messenger, PYPT task_chain);
   
  void dispatch(PYPT acceptor_dict, PYPT event, PYPT sent_args, PYPT found_watch);
  
  static void make_global_ptr();
   
  PyObject *callbacks; // event_name->obj_msgr_id->callback_info
  PyObject *object_events; // obj_msgr_id->set(event_name)
  PyObject *id2object; // obj_msgr_id->listener_object
  PyObject *event_queues_by_task_chain;
  
  uint64_t messenger_id_gen = 0;
  
  ReMutex _lock;
  
  static Messenger *_global_ptr;

public:
  static TypeHandle get_class_type() { return _type_handle; }

  static void init_type() {
    TypedReferenceCount::init_type();
    register_type(_type_handle, "Messenger", TypedReferenceCount::get_class_type());
  }

  virtual TypeHandle get_type() const { return get_class_type(); }
  virtual TypeHandle force_init_type() { init_type(); return get_class_type(); }

private:
  static TypeHandle _type_handle;
};

class EXPCL_DIRECT_SHOWBASE MessengerChainTask : public AsyncTask {
 public:
   typedef AsyncTask::DoneStatus TaskFunc(MessengerChainTask *task, PT(Messenger) messenger, PYPT task_chain);
 
   MessengerChainTask(const std::string &name = std::string(), PT(Messenger) messenger = nullptr);
   MessengerChainTask(const std::string &name, TaskFunc *function, PT(Messenger) messenger, PYPT task_chain);
   ALLOC_DELETED_CHAIN(MessengerChainTask);
 
   INLINE void set_function(TaskFunc *function);
   INLINE TaskFunc *get_function() const;
   
   INLINE void set_task_chain(PYPT task_chain);
   INLINE PYPT get_task_chain() const;
 
 protected:
   virtual bool is_runnable();
   virtual AsyncTask::DoneStatus do_task();
 
 private:
   TaskFunc *_function;
   PT(Messenger) _messenger;
   PYPT _task_chain;
 
 public:
   static TypeHandle get_class_type() { return _type_handle; }

   static void init_type() {
     AsyncTask::init_type();
     register_type(_type_handle, "MessengerChainTask", AsyncTask::get_class_type());
   }

   virtual TypeHandle get_type() const { return get_class_type(); }
   virtual TypeHandle force_init_type() { init_type(); return get_class_type(); }
 
 private:
   static TypeHandle _type_handle;
 };

#include "messenger.I"

#endif // HAVE_PYTHON

#endif // MESSENGER_H