/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file pythonPointerTo.I
 * @author Prince Frizzy
 * @date 2023-09-15
 */
 
/**
 *
 */
ALWAYS_INLINE PythonPointerTo::
PythonPointerTo(PyObject *ptr) noexcept {
  _ptr = ptr;
  Py_XINCREF(_ptr);
}

/**
 *
 */
INLINE PythonPointerTo::
PythonPointerTo(const PythonPointerTo &copy) {
  _ptr = copy._ptr;
  Py_XINCREF(_ptr);
}

/**
 *
 */
INLINE PythonPointerTo::
PythonPointerTo(PythonPointerTo &&from) noexcept {
  _ptr = from._ptr;
  from._ptr = nullptr;
}

/**
 *
 */
INLINE PythonPointerTo::
~PythonPointerTo() {
  Py_XDECREF(_ptr);
  _ptr = nullptr;
}

/**
 * Returns true if the PythonPointerTo is a NULL pointer, false otherwise.  (Direct
 * comparison to a NULL pointer also works.)
 */
constexpr bool PythonPointerTo::
is_null() const {
  return _ptr == nullptr;
}

/**
 *
 */
INLINE size_t PythonPointerTo::
get_hash() const {
  return (size_t)_ptr;
}

/**
 *
 */
INLINE bool PythonPointerTo::
operator < (const PyObject *other) const {
  return _ptr < other;
}

/**
 *
 */
INLINE bool PythonPointerTo::
operator < (const PythonPointerTo &other) const {
  return _ptr < other._ptr;
}

/**
 *
 */
INLINE bool PythonPointerTo::
operator == (PyObject *other) {
  return _ptr == other;
}

/**
 *
 */
INLINE bool PythonPointerTo::
operator == (const PythonPointerTo &other) const {
  return _ptr == other._ptr;
}


/**
 *
 */
INLINE bool PythonPointerTo::
operator != (PyObject *other) {
  return _ptr != other;
}

/**
 *
 */
INLINE bool PythonPointerTo::
operator != (const PythonPointerTo &other) const {
  return _ptr != other._ptr;
}

/**
 *
 */
INLINE PythonPointerTo &PythonPointerTo::
operator = (PyObject *ptr) {
  this->reassign(ptr);
  return *this;
}

/**
 *
 */
INLINE PythonPointerTo &PythonPointerTo::
operator = (const PythonPointerTo &copy) {
  this->reassign(copy);
  return *this;
}

/**
 *
 */
INLINE PythonPointerTo &PythonPointerTo::
operator = (PythonPointerTo &&from) noexcept {
  this->reassign(std::move(from));
  return *this;
}

/**
 *
 */
constexpr PyObject &PythonPointerTo::
operator *() const noexcept {
  return *this->_ptr;
}

/**
 *
 */
constexpr PyObject *PythonPointerTo::
operator -> () const noexcept {
  return this->_ptr;
}

/**
 *
 */
constexpr PythonPointerTo::
operator PyObject * () const noexcept {
  return this->_ptr;
}

/**
 *
 */
INLINE PyObject *&PythonPointerTo::
cheat() {
  return this->_ptr;
}

/**
 *
 */
INLINE void PythonPointerTo::
swap(PythonPointerTo &other) noexcept {
  PyObject *temp = _ptr;
  _ptr = other._ptr;
  other._ptr = temp;
}

/**
 *
 */
INLINE void PythonPointerTo::
reassign(PythonPointerTo &&from) noexcept {
  // Protect against self-move-assignment.
  if (from._ptr == this->_ptr) { return; }
  
  PyObject *old_ptr = this->_ptr;

  this->_ptr = from._ptr;
  from._ptr = nullptr;
  
  // Dereference the old pointer. 
  Py_XDECREF(old_ptr);
}

/**
 *
 */
INLINE void PythonPointerTo::
reassign(PyObject *ptr) {
  // Protect against self-assignment.
  if (ptr == _ptr) { return; }
  
  // First save the old pointer; we won't delete it until we have assigned
  // the new one.  We do this just in case there are cascading effects from
  // deleting this pointer that might inadvertently delete the new one.
  // (Don't laugh--it's happened!)
  PyObject *old_ptr = _ptr;

  _ptr = ptr;
  Py_XINCREF(ptr);
    
  // Dereference the old pointer. 
  Py_XDECREF(old_ptr);
}

/**
 *
 */
INLINE void PythonPointerTo::
reassign(const PythonPointerTo &copy) {
  // Protect against self-assignment.
  if (copy._ptr == _ptr) { return; }
  
  // First save the old pointer; we won't delete it until we have assigned
  // the new one.  We do this just in case there are cascading effects from
  // deleting this pointer that might inadvertently delete the new one.
  // (Don't laugh--it's happened!)
  PyObject *old_ptr = _ptr;
  PyObject *new_ptr = copy._ptr;

  _ptr = copy._ptr;
  Py_XINCREF(new_ptr);

  // Dereference the old pointer. 
  Py_XDECREF(old_ptr);
}

/**
 *
 */
ALWAYS_INLINE void PythonPointerTo::
clear() {
  reassign(nullptr);
}

/**
 * Returns an ordinary pointer instead of a PythonPointerTo.  Useful to work around
 * compiler problems, particularly for implicit upcasts.
 */
constexpr PyObject *PythonPointerTo::
p() const noexcept {
  return this->_ptr;
}



/**
 *
 */
INLINE void PythonPointerTo::
output(std::ostream &out) const {
  out << _ptr;
  if (_ptr != nullptr) {
    out << ":" << Py_REFCNT((PyObject *)_ptr);
  }
}


/**
 * Creates a PythonPointerTo by stealing a strong reference to the Python Object.
 * This is done so things like PyList_New() can be used
 * without having to manually decrement the reference.
 */
ALWAYS_INLINE PythonPointerTo PythonPointerTo::inplace(PyObject *ptr) noexcept {
  PythonPointerTo r;
  r._ptr = ptr;
  
  return r;
}