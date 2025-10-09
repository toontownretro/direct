/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file messenger.cxx
 * @author Prince Frizzy
 * @date 2023-09-16
 */
 
#include "messenger.h"

// This is only ever actually needed if we compile for Python.
#ifdef HAVE_PYTHON

TypeHandle Messenger::_type_handle;
TypeHandle MessengerChainTask::_type_handle;

Messenger *Messenger::_global_ptr;

/*
 *
 */
Messenger::Messenger() : _lock("Messenger::_lock") {
 /**
  * One is keyed off the event name. It has the following structure::
  * 
  *    {event1: {object1: [method, extraArgs, persistent],
  *               object2: [method, extraArgs, persistent]},
  *     event2: {object1: [method, extraArgs, persistent],
  *               object2: [method, extraArgs, persistent]}}
  * 
  * This dictionary allows for efficient callbacks when the
  * messenger hears an event.
  * 
  * A second dictionary remembers which objects are accepting which
  * events. This allows for efficient ignoreAll commands.
  * 
  * Or, for an example with more real data::
  * 
  *    {'mouseDown': {avatar: [avatar.jump, [2.0], 1]}}
  */
  
  callbacks = PyDict_New();
  object_events = PyDict_New();
  id2object = PyDict_New();
  event_queues_by_task_chain = PyDict_New();
}

/*
 *
 */
Messenger::~Messenger() {
  PyDict_Clear(callbacks);
  PyDict_Clear(object_events);
  PyDict_Clear(id2object);
  PyDict_Clear(event_queues_by_task_chain);
  
  Py_XDECREF(callbacks);
  Py_XDECREF(object_events);
  Py_XDECREF(id2object);
  Py_XDECREF(event_queues_by_task_chain);
}

/*
 * Returns new reference to tuple.
 */
PyObject *Messenger::get_messenger_id(PYPT object) {
  ReMutexHolder holder(_lock);
  
  // If the object isn't valid, Then return a empty pointer!
  if (!object) { return Py_None; }
  
  // Check if the PyObject already has a messenger id.
  // If it does not, Then we give it one.
  PyObject *msgr_id = PyObject_GetAttrString(object, "_MSGRmessengerId");
  if (msgr_id && !Py_IsNone(msgr_id)) { return msgr_id; }
  Py_XDECREF(msgr_id);

  // Get the classname of the object.
  PyObject *obj_class = PyObject_GetAttrString(object, "__class__");
  PyObject *obj_class_name = nullptr;
  if (obj_class) {
    obj_class_name = PyObject_GetAttrString(obj_class, "__name__");
    Py_DECREF(obj_class);
  }
  if (!obj_class_name) {
    obj_class_name = Py_None;
    Py_INCREF(obj_class_name);
  }
  // Build our new messenger id for the object.
  PyObject *new_msgr_id = Py_BuildValue("(OK)", obj_class_name, messenger_id_gen);
  Py_XDECREF(obj_class_name);
  // Assign the messenger id to the object.
  PyObject_SetAttrString(object, "_MSGRmessengerId", new_msgr_id);
  // Incremenmt our id gen.
  ++messenger_id_gen;
  return new_msgr_id;
}

/*
 * Store reference-counted reference to object in case we need to
 * retrieve it later.  Assumes lock is held.
 */
void Messenger::store_object(PYPT object) {
  ReMutexHolder holder(_lock);
  
  // Get the messenger id for the object in question, If we fail to get one?
  // Then the object isn't a valid object to store and we just abort.
  PyObject *id = get_messenger_id(object);
  if (!id || Py_IsNone(id)) {
    Py_XDECREF(id); 
    return; 
  }
  
  // Check if the object is already stored, If so? Increase the ref count. If not?
  // Add it to the storage dictionary.
  PyObject *item = PyDict_GetItem(id2object, id);
  Py_XDECREF(id);
  if (item) {
    uint64_t cnt = 1;
    PyObject *ref_cnt = PyObject_GetAttrString(item, "_refCnt");
    if (ref_cnt) {
      cnt = PyLong_AsUnsignedLongLong(ref_cnt);
      ++cnt;
      Py_DECREF(ref_cnt);
    }
    
    // Store the reference count on the object for ease of use. Also allows people in Python to check the amount of 
    // references the object has to it in the Messenger.
    PyObject *cnt_obj = PyLong_FromUnsignedLongLong(cnt);
    if (cnt_obj) {
      PyObject_SetAttrString(item, "_refCnt", cnt_obj);
      Py_DECREF(cnt_obj);
    }
  } else {
    // Store the reference count on the object for ease of use. Also allows people in Python to check the amount of 
    // references the object has to it in the Messenger.
    PyObject *cnt_obj = PyLong_FromUnsignedLongLong(1);
    if (cnt_obj) {
      PyObject_SetAttrString(object, "_refCnt", cnt_obj);
      Py_DECREF(cnt_obj);
    }
    
    int e = PyDict_SetItem(id2object, id, object);
    if (e == -1) { PyErr_Print(); }
  }
}

/*
 *
 */
PyObject *Messenger::get_object(PYPT id) {
  ReMutexHolder holder(_lock);
  
  PyObject *item = PyDict_GetItem(id2object, id);
  if (!item) { item = Py_None; }
  return item;
}

/*
 *
 */
PyObject *Messenger::get_objects() {
  ReMutexHolder holder(_lock);
  
  PyObject *list = PyList_New(0);
  if (!list) {
    PyErr_Print(); 
    return Py_None; 
  }
  
  PyObject *key = nullptr, *value = nullptr;
  Py_ssize_t pos = 0;
  
  while (PyDict_Next(id2object, &pos, &key, &value)) {
    int e = PyList_Append(list, value);
    if (e == -1) { PyErr_Print(); break; }
  }
  
  return list;
}

/*
 *
 */
Py_ssize_t Messenger::get_num_listeners(PYPT event) {
  ReMutexHolder holder(_lock);
  
  PyObject *event_callbacks = PyDict_GetItem(callbacks, event);
  if (!event_callbacks || !PyDict_Check(event_callbacks)) { return 0; }
  
  return PyDict_Size(event_callbacks);
}

/*
 *
 */
PyObject *Messenger::get_events() {
  ReMutexHolder holder(_lock);
  
  // Get all of the keys from our callback dict.
  PyObject *keys = PyDict_Keys(callbacks);
  if (!keys) {
    PyErr_Print();
    return Py_None;
  }
  
  // Create a list to copy the keys into.
  PyObject *keys_cpy = PyList_New(PyList_Size(keys));
  // If the list failed to be allocated/created, Return None.
  if (!keys_cpy) {
    Py_DECREF(keys);
    PyErr_Print();
    return Py_None;
  }
  
  // Copy the keys into a new list to prevent the original list from being
  // modified.
  for (Py_ssize_t i = 0; i < PyList_Size(keys); ++i) {
    PyObject *item = PyList_GetItem(keys, i);
    if (!item) { break; }
    Py_INCREF(item);
    
    int e = PyList_SetItem(keys_cpy, i, item);
    if (e == -1) { PyErr_Print(); break; }
  }
  
  Py_DECREF(keys);
  return keys_cpy;
}

/*
 *
 */
void Messenger::release_object(PYPT object) {
  ReMutexHolder holder(_lock);
  
  // Get the messenger id for the object in question, If we fail to get one?
  // Then the object isn't a valid object to release and we just abort.
  PyObject *id = get_messenger_id(object);
  if (!id || Py_IsNone(id)) {
    Py_XDECREF(id);
    return; 
  }
  
  // Check if the object is already stored. If not we abort.
  PyObject *item = PyDict_GetItem(id2object, id);
  if (!item) {
    Py_DECREF(id);
    return;
  }
  
  PyObject *ref_cnt = PyObject_GetAttrString(item, "_refCnt");
  if (!ref_cnt) { // TODO: Raise an error/exception if this happens.
    Py_DECREF(id);
    return; 
  }
  
  uint64_t cnt = PyLong_AsUnsignedLongLong(ref_cnt);
  --cnt;
  Py_DECREF(ref_cnt);
  
  
  // If the count is at or dips below zero. The object is no longer stored.
  if (cnt <= 0) {
    // Remove the attribute from the object, It's not needed anymore.
    PyObject_DelAttrString(item, "_refCnt");
    // Remove the oject and id from the dictionary.
    PyDict_DelItem(id2object, id);
  } else {
    // Set the new reference count on our object.
    PyObject *cnt_obj = PyLong_FromUnsignedLongLong(cnt);
    if (cnt_obj) {
      PyObject_SetAttrString(item, "_refCnt", cnt_obj);
      Py_DECREF(cnt_obj);
    }
  }
  
  Py_DECREF(id);
}

/*
 * Returns a future that is triggered by the given event name.  This
 * will function only once.
 */
PyObject *Messenger::future(PYPT event) {
  // TODO: Reference the Event Manager and get a future for a event.
  return Py_None;
}

/*
 * accept(string, DirectObject, Function, List, Boolean)
 * 
 * Make this object accept this event. When the event is
 * sent (using Messenger.send or from C++), method will be executed,
 * optionally passing in extraArgs.
 * 
 * If the persistent flag is set, it will continue to respond
 * to this event, otherwise it will respond only once.
 */
void Messenger::accept(PYPT event, PYPT object, PYPT method, PYPT extra_args, bool persistent) {
  ReMutexHolder holder(_lock);
  
  // Make sure that method is callable.
  if (!PyObject_HasAttrString(method, "__call__")) { return; }
  
  // Make sure extra_args is a list, tuple or set.
  if (!PyList_Check(extra_args) && !PyTuple_Check(extra_args) && !PySet_Check(extra_args)) { return; }
  
  PyObject *id = get_messenger_id(object);
  
  PyObject *acceptor_dict = PyDict_SetDefault(callbacks, event, PyDict_New());
  
  /*
  # Make sure we are not inadvertently overwriting an existing event
  # on this particular object.
  if id in acceptorDict:
    # TODO: we're replacing the existing callback. should this be an error?
    if notifyDebug:
      oldMethod = acceptorDict[id][0]
      if oldMethod == method:
        self.notify.warning("object: %s was already accepting: \"%s\" with same callback: %s()" % (object.__class__.__name__, safeRepr(event), method.__name__))
      else:
        self.notify.warning("object: %s accept: \"%s\" new callback: %s() supplanting old callback: %s()" % (object.__class__.__name__, safeRepr(event), method.__name__, oldMethod.__name__))
  */
  
  
  PyDict_SetItem(acceptor_dict, id, Py_BuildValue("[OOi]", method.p(), extra_args.p(), persistent));
  
  // Remember that this object is listening for this event.
  PyObject *event_dict = PyDict_SetDefault(object_events, id, PyDict_New());
  Py_XDECREF(id);
  if (!PyDict_Contains(event_dict, event)) {
    store_object(object);
    PyDict_SetItem(event_dict, event, Py_None);
  }
}

/*
 * ignore(string, DirectObject)
 * Make this object no longer respond to this event.
 * It is safe to call even if it was not already accepting
 */
void Messenger::ignore(PYPT event, PYPT object) {
  ReMutexHolder holder(_lock);
  
  PyObject *id = get_messenger_id(object);
  
  // Find the dictionary of all the objects accepting this event.
  PyObject *acceptor_dict = PyDict_GetItem(callbacks, event);
  // If this object is there, delete it from the dictionary
  if (acceptor_dict && PyDict_Contains(acceptor_dict, id)) {
    PyDict_DelItem(acceptor_dict, id);
    // If this dictionary is now empty, remove the event
    // entry from the Messenger alltogether.
    if (PyDict_Size(acceptor_dict) <= 0) { PyDict_DelItem(callbacks, event); }
  }
  
  // This object is no longer listening for this event.
  PyObject *event_dict = PyDict_GetItem(object_events, id);
  if (event_dict && PyDict_Contains(event_dict, event)) {
    PyDict_DelItem(event_dict, event);
    if (PyDict_Size(event_dict) <= 0) { PyDict_DelItem(object_events, id); }
    
    release_object(object);
  }
  
  Py_XDECREF(id);
}

/*
 * ignore_all(DirectObject)
 * Make this object no longer respond to any events it was accepting.
 * Useful for cleanup.
 */
void Messenger::ignore_all(PYPT object) {
  ReMutexHolder holder(_lock);
  
  PyObject *id = get_messenger_id(object);
  
  // Get the list of events this object is listening to.
  PyObject *event_dict = PyDict_GetItem(object_events, id);
  if (!event_dict) { 
    Py_XDECREF(id);
    return; 
  }
  
  // Get and iterate all of the keys from our event dict.
  PyObject *keys = PyDict_Keys(event_dict);
  for (Py_ssize_t i = 0; i < PyList_Size(keys); ++i) {
    PyObject *event = PyList_GetItem(keys, i);
    if (!event) { break; }
    
    // Find the dictionary of all the objects accepting this event.
    PyObject *acceptor_dict = PyDict_GetItem(callbacks, event);
    // If this object is there, delete it from the dictionary.
    if (acceptor_dict && PyDict_Contains(acceptor_dict, id)) {
      PyDict_DelItem(acceptor_dict, id);
      // If this dictionary is now empty, remove the event
      // entry from the Messenger alltogether.
      if (PyDict_Size(acceptor_dict) <= 0) { PyDict_DelItem(callbacks, event); }
    }
    
    release_object(object);
  }
  
  PyDict_DelItem(object_events, id);
  
  Py_XDECREF(keys);
  Py_XDECREF(id);
}

/*
 * get_all_accepting(DirectObject)
 * Returns the list of all events accepted by the indicated object.
 */
PyObject *Messenger::get_all_accepting(PYPT object) {
  ReMutexHolder holder(_lock);
  
  PyObject *id = get_messenger_id(object);
  
  // Get the list of events this object is listening to
  PyObject *event_dict = PyDict_GetItem(object_events, id);
  Py_XDECREF(id);
  if (!event_dict) {
    PyObject *empty_list = PyList_New(0);
    return empty_list;
  }
  
  // Get all of the keys from our event dict.
  PyObject *keys = PyDict_Keys(event_dict);
  
  // Create a list to copy the keys into.
  PyObject *keys_cpy = PyList_New(PyList_Size(keys));
  // If the list failed to be allocated/created, Return None.
  if (!keys_cpy) {
    Py_XDECREF(keys);
    PyErr_Print(); 
    return Py_None; 
  }
  
  // Copy the keys into a new list to prevent the original list from being
  // modified.
  for (Py_ssize_t i = 0; i < PyList_Size(keys); ++i) {
    PyObject *item = PyList_GetItem(keys, i);
    if (!item) { break; }
    Py_INCREF(item);
    
    int e = PyList_SetItem(keys_cpy, i, item);
    if (e == -1) { PyErr_Print(); break; }
  }
  
  Py_XDECREF(keys);
  return keys_cpy;
}

/*
 * is_accepting(string, DirectOject)
 * Returns if this object is accepting this event.
 */
bool Messenger::is_accepting(PYPT event, PYPT object) {
  ReMutexHolder holder(_lock);
  
  PyObject *id = get_messenger_id(object);
  
  // Find the dictionary of all the objects accepting this event.
  PyObject *acceptor_dict = PyDict_GetItem(callbacks, event);
  // If this object is there, return true.
  if (acceptor_dict && PyDict_Contains(acceptor_dict, id)) {
    Py_XDECREF(id);
    return true;
  }
  
  // Return false otherwise.
  Py_XDECREF(id);
  return false;
}

/*
 * is_ignoring(string, DirectOject)
 * Returns if this object is ignoring this event.
 */
bool Messenger::is_ignoring(PYPT event, PYPT object) {
  return !is_accepting(event, object);
}

/*
 * who_accepts(string)
 * Return objects accepting the given event.
 */
PyObject *Messenger::who_accepts(PYPT event) {
  ReMutexHolder holder(_lock);
  
  // Find the dictionary of all the objects accepting this event,
  // and if it's found? Return it.
  PyObject *acceptor_dict = PyDict_GetItem(callbacks, event);
  if (acceptor_dict) { return acceptor_dict; }
  
  // If not? Return None.
  return Py_None;
}

/*
 * send(string, list, string)
 * Send this event, optionally passing in arguments.
 *
 * Args:
 *   event (str): The name of the event.
 *   sentArgs (list): A list of arguments to be passed along to the handlers listening to this event.
 *   taskChain (str, optional): If not None, the name of the task chain which should receive the event.  
 *      If None, then the event is handled immediately. Setting a non-None taskChain will defer
 *      the event (possibly till next frame or even later) and create a
 *      new, temporary task within the named taskChain, but this is the
 *      only way to send an event across threads.
 */
void Messenger::send(PYPT event, PYPT sent_args, PYPT task_chain) {
  ReMutexHolder holder(_lock);
  
  if (!event || event == Py_None) { return; }
  if (!sent_args) { sent_args = PyList_New(0); }
  if (!task_chain) { task_chain = Py_None; }
  
  /*
  if Messenger.notify.getDebug() and not self.quieting.get(event):
    assert Messenger.notify.debug('sent event: %s sentArgs = %s, taskChain = %s' % (event, sentArgs, taskChain))
  */
  
  /*
  PyObject *event_str_obj = PyObject_Str(event);
  const char *event_str = PyUnicode_AsUTF8(event_str_obj);
  
  PyObject *sent_args_str_obj = PyObject_Str(sent_args);
  const char *sent_args_str = PyUnicode_AsUTF8(sent_args_str_obj);
  
  PyObject *task_chain_str_obj = PyObject_Str(task_chain);
  const char *task_chain_str = PyUnicode_AsUTF8(task_chain_str_obj);
  
  std::cout << (int32_t)Py_REFCNT(event.p()) << " " <<  (int32_t)Py_REFCNT(sent_args.p()) << " " << (int32_t)Py_REFCNT(task_chain.p()) << std::endl;
  std::cout << "sent event: " << event_str << ", sentArgs = " << sent_args_str << ", taskChain = " << task_chain_str <<  std::endl;
  
  Py_XDECREF(event_str_obj);
  Py_XDECREF(sent_args_str_obj);
  Py_XDECREF(task_chain_str_obj);
  */
  
  bool found_watch = false;
  /*
  if __debug__:
    if self.__isWatching:
      for i in self.__watching:
        if str(event).find(i) >= 0:
          foundWatch = True
          break
  */
  
  PyObject *acceptor_dict = PyDict_GetItem(callbacks, event);
  if (!acceptor_dict) {
    /*
    if __debug__:
      if foundWatch:
        print("Messenger: \"%s\" was sent, but no function in Python listened."%(event,))
    */
    return; 
  }
  
  if (task_chain && !Py_IsNone(task_chain)) {
    // Queue the event onto the indicated task chain.
    PyObject *queue = PyDict_SetDefault(event_queues_by_task_chain, task_chain, PyList_New(0));
    PyObject *event_info = PyTuple_Pack(4, acceptor_dict, event.p(), sent_args.p(), found_watch);
    int result = PyList_Append(queue, event_info);
    Py_XDECREF(event_info);
    if (result == -1) {
      PyErr_Print();
      return; 
    }
    
    Py_ssize_t size = PyList_Size(queue);
    if (size == 1) {
      // If this is the first (only) item on the queue,
      // spawn the task to empty it.
      PyObject *task_chain_str_obj = PyObject_Str(task_chain);
      const char *task_chain_str = PyUnicode_AsUTF8(task_chain_str_obj);
      std::string task_chain_name(task_chain_str);
      Py_XDECREF(task_chain_str_obj);
      
      std::string task_name("Messenger-" + task_chain_name);
      PT(MessengerChainTask) _chain_task = new MessengerChainTask(task_name, &Messenger::task_chain_dispatch, this, task_chain);
      PT(AsyncTaskManager) task_mgr = AsyncTaskManager::get_global_ptr();
      task_mgr->add(_chain_task);
    }
  } else {
    // Handle the event immediately.
    PyObject *found_watch_object = PyBool_FromLong(found_watch);
    dispatch(acceptor_dict, event, sent_args, found_watch_object);
    Py_XDECREF(found_watch_object);
  }
}

/*
 * This task is spawned each time an event is sent across
 * task chains.  Its job is to empty the task events on the queue
 * for this particular task chain.  This guarantees that events
 * are still delivered in the same order they were sent.
 */
AsyncTask::DoneStatus Messenger::task_chain_dispatch(MessengerChainTask *task, PT(Messenger) messenger, PYPT task_chain) {
  //ReMutexHolder holder(messenger->_lock);
  
  while (true) {
    PyObject *event_queues_by_task_chain = messenger->event_queues_by_task_chain;
    
    PyObject *queue = PyDict_GetItem(event_queues_by_task_chain, task_chain);
    if (!queue) {
      // There is no more events in the queue or it doesn't exist, Return that our task is over.
      return AsyncTask::DoneStatus::DS_done;
    }
    
    // Get the event tuple.
    PyObject *event_tuple = PyList_GetItem(queue, 0);
    // Remove the event tuple from the list.
    PyList_SetSlice(queue, 0, 1, NULL);
    
    Py_ssize_t queue_size = PyList_Size(queue);
    if (queue_size <= 0) {
      // The queue is empty, we're done with it.
      PyDict_DelItem(event_queues_by_task_chain, task_chain);
    }
    
    if (!event_tuple) {
      // No event; we're done.
      return AsyncTask::DoneStatus::DS_done;
    }
    
    // Get all of the arguments for dispatch.
    PyObject *acceptor_dict = PyTuple_GetItem(event_tuple, 0);
    PyObject *event = PyTuple_GetItem(event_tuple, 1);
    PyObject *sent_args = PyTuple_GetItem(event_tuple, 2);
    PyObject *found_watch = PyTuple_GetItem(event_tuple, 3);
    
    messenger->dispatch(acceptor_dict, event, sent_args, found_watch);
  }
}

void Messenger::dispatch(PYPT acceptor_dict, PYPT event, PYPT sent_args, PYPT found_watch) {
  //ReMutexHolder holder(_lock);
  _lock.acquire();
  
#if defined(HAVE_THREADS) && !defined(SIMPLE_THREADS)
  PyGILState_STATE gstate = PyGILState_Ensure();
#endif
  
  PyObject *result = nullptr;
  
  PyObject *id = nullptr, *call_info = nullptr;
  Py_ssize_t pos = 0;
  
  while (PyDict_Next(acceptor_dict, &pos, &id, &call_info)) {
    // We have to make this apparently redundant check, because
    // it is possible that one object removes its own hooks
    // in response to a handler called by a previous object.
    //
    // NOTE: There is no danger of skipping over objects due to
    // modifications to acceptor_dict, since the for.. in above
    // iterates over a list of objects that is created once at
    // the start
    if (!call_info || Py_IsNone(call_info)) { continue; }
    
    PyObject *method = PyList_GetItem(call_info, 0);
    PyObject *extra_args = PyList_GetItem(call_info, 1);
    PyObject *persistent = PyList_GetItem(call_info, 2);
    
    // If this object was only accepting this event once,
    // remove it from the dictionary
    if (Py_IsFalse(persistent) && PyDict_Contains(object_events, id)) {
      // This object is no longer listening for this event.
      PyObject *event_dict = PyDict_GetItem(object_events, id);
      if (event_dict && PyDict_Contains(event_dict, event)) {
        PyDict_DelItem(event_dict, event);
        Py_ssize_t size = PyDict_Size(event_dict);
        // If there's no more events. Remove 
        if (size == 0) { PyDict_DelItem(object_events, id); }
        // Release the object associated with the id. 
        release_object(get_object(id));
      }
      
      PyDict_DelItem(acceptor_dict, id);
      
      // If the dictionary at this event is now empty, remove
      // the event entry from the Messenger altogether.
      if (PyDict_Contains(callbacks, event) && PyDict_Size(PyDict_GetItem(callbacks, event)) == 0) {
        PyDict_DelItem(callbacks, event);
      }
    }
    
    /*
    if __debug__:
      if foundWatch:
        print("Messenger: \"%s\" --> %s%s"%(event, self.__methodRepr(method), tuple(extraArgs + sentArgs)))
    */
    
    // It is important to make the actual call here, after
    // we have cleaned up the accept hook, because the
    // method itself might call accept() or accept_once()
    // again.
    //assert(PyObject_HasAttrString(method, "__call__") && PyCallable_Check(method));
    if (!PyObject_HasAttrString(method, "__call__") || !PyCallable_Check(method)) { continue; }
    
    // Add our extra args and sent args to a list and then convert it into a tuple.
    PyObject *args_list = PyList_New(0);
    
    // Add our extra arguments to the list first.
    PyObject *iterator = PyObject_GetIter(extra_args);
    if (iterator != nullptr) {
      PyObject *item = nullptr;
      while ((item = PyIter_Next(iterator))) {
        PyList_Append(args_list, item);
        Py_XDECREF(item);
      }
      
      Py_DECREF(iterator);
      
      if (PyErr_Occurred()) { PyErr_Print(); continue; }
    }
    
    // Add our sent arguments to the list second.
    iterator = PyObject_GetIter(sent_args);
    if (iterator != nullptr) {
      PyObject *item = nullptr;
      while ((item = PyIter_Next(iterator))) {
        PyList_Append(args_list, item);
        Py_XDECREF(item);
      }
      
      Py_DECREF(iterator);
      
      if (PyErr_Occurred()) { PyErr_Print(); continue; }
    }
    
    // Get the size of the list and create a tuple of that size.
    Py_ssize_t size = PyList_Size(args_list);
    PyObject *args = PyTuple_New(size);
    
    // Add all of the arguments from the list to the tuple.
    for (Py_ssize_t i = 0; i < size; i++) {
      PyObject *item = PyList_GetItem(args_list, i);
      if (!item || PyErr_Occurred()) { PyErr_Print(); item = Py_None; }
      Py_INCREF(item);
      
      PyTuple_SetItem(args, i, item);
    }
    
    Py_XDECREF(args_list);

    // Mow we can call the function object and pass in our converted args!
    
    _lock.release(); // Release the lock temporarily while we call the method.
    result = PyObject_CallObject(method, args);
    _lock.acquire();
    
    Py_XDECREF(args);
    if (PyErr_Occurred()) {
      Py_XDECREF(result);
      PyErr_Print();
      continue;
    }
    
    /*
    if (result && PyObject_HasAttrString(result, "cr_await")) {
      // It's a coroutine, so schedule it with the task manager.
      PT(AsyncTaskManager) task_mgr = AsyncTaskManager::get_global_ptr();
      PT(PythonTask) task = new PythonTask(result);
      task_mgr->add(task);
    }
    */
    
    Py_XDECREF(result);
  }
  
#if defined(HAVE_THREADS) && !defined(SIMPLE_THREADS)
  PyGILState_Release(gstate);
#endif

  _lock.release();
}

 /**
  * Start fresh with clear dictionaries.
  */
void Messenger::clear() {
  ReMutexHolder holder(_lock);

  PyDict_Clear(callbacks);
  PyDict_Clear(object_events);
  PyDict_Clear(id2object);
}

bool Messenger::is_empty() {
  return PyDict_Size(callbacks) == 0;
}

 /**
  * Called once per application to create the global messenger object.
  */
void Messenger::make_global_ptr() {
  nassertv(_global_ptr == nullptr);
 
  init_memory_hook();
  _global_ptr = new Messenger();
  _global_ptr->ref();
}

/**
 *
 */
MessengerChainTask::MessengerChainTask(const std::string &name, PT(Messenger) messenger) : AsyncTask(name), _messenger(messenger) 
{
  _function = nullptr;
}

/**
 *
 */
MessengerChainTask::
MessengerChainTask(const std::string &name, TaskFunc *function, PT(Messenger) messenger, PYPT task_chain) : AsyncTask(name), _messenger(messenger), _task_chain(task_chain)
{
  _function = function;
}

/**
 * Override this function to return true if the task can be successfully
 * executed, false if it cannot.  Mainly intended as a sanity check when
 * attempting to add the task to a task manager.
 *
 * This function is called with the lock held.
 */
bool MessengerChainTask::is_runnable() {
  return (_function != nullptr && _messenger != nullptr && _task_chain != nullptr);
}

/**
 * Override this function to do something useful for the task.
 *
 * This function is called with the lock *not* held.
 */
AsyncTask::DoneStatus MessengerChainTask::do_task() {
  nassertr(_function != nullptr, DS_interrupt);
  return (*_function)(this, _messenger, _task_chain);
}

#endif // HAVE_PYTHON