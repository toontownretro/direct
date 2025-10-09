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
 * @date 2023-09-17
 */
 
 /**
  * accept(string, DirectObject, Function)
  * 
  * Make this object accept this event. When the event is
  * sent (using Messenger.send or from C++), method will be executed,
  * optionally passing in extraArgs.
  * 
  * If the persistent flag is set, it will continue to respond
  * to this event, otherwise it will respond only once.
  */
INLINE void Messenger::accept(PYPT event, PYPT object, PYPT method) {
  ReMutexHolder holder(_lock);
  
  PYPT extra_args = PYPT::inplace(PyList_New(0));
  if (!extra_args) { PyErr_Print(); return; }
  
  accept(event, object, method, extra_args, true);
}
 
 /**
  * accept(string, DirectObject, Function, List)
  * 
  * Make this object accept this event. When the event is
  * sent (using Messenger.send or from C++), method will be executed,
  * optionally passing in extraArgs.
  * 
  * If the persistent flag is set, it will continue to respond
  * to this event, otherwise it will respond only once.
  */
INLINE void Messenger::accept(PYPT event, PYPT object, PYPT method, PYPT extra_args) {
  accept(event, object, method, extra_args, true);
}

/*
 * send(string)
 * Send this event, optionally passing in arguments.
 *
 * Args:
 *   event (str): The name of the event.
 */
INLINE void Messenger::send(PYPT event) {
  send(event, nullptr, nullptr);
}

/*
 * send(string, list)
 * Send this event, optionally passing in arguments.
 *
 * Args:
 *   event (str): The name of the event.
 *   sentArgs (list): A list of arguments to be passed along to the handlers listening to this event.
 */
INLINE void Messenger::send(PYPT event, PYPT sent_args) {
  send(event, sent_args, nullptr);
}


 /**
  * Returns a pointer to the global Messenger.  This is the
  * Messenger that most code should use for sending messages.
  */
INLINE Messenger *Messenger::get_global_ptr() {
  if (_global_ptr == nullptr) {
    make_global_ptr();
  }
  return _global_ptr;
}

/**
 * Replaces the function that is called when the task runs.
 */
INLINE void MessengerChainTask::set_function(MessengerChainTask::TaskFunc *function) {
  _function = function;
}

/**
 * Returns the function that is called when the task runs.
 */
INLINE MessengerChainTask::TaskFunc *MessengerChainTask::get_function() const {
  return _function;
}

/**
 * Replaces the task chain that is used when the task runs.
 */
INLINE void MessengerChainTask::set_task_chain(PYPT task_chain) {
  _task_chain = task_chain;
}

/**
 * Returns the task chain that is used when the task runs.
 */
INLINE PYPT MessengerChainTask::get_task_chain() const {
  return _task_chain;
}