/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file pythonPointerTo.h
 * @author Prince Frizzy
 * @date 2023-09-15
 */
 
#ifndef PYTHONPOINTERTO_H
#define PYTHONPOINTERTO_H

#include "directbase.h"
#include "pnotify.h"
#include "memoryBase.h"
#include "atomicAdjust.h"
#include "referenceCount.h"
#include "memoryUsage.h"
#include "config_express.h"

#include <algorithm>

// This is only ever actually needed if we compile for Python.
#ifdef HAVE_PYTHON

#include "py_panda.h"

class EXPCL_DIRECT_DIRECTBASE PythonPointerTo : public MemoryBase {
PUBLISHED:
  ALWAYS_INLINE constexpr PythonPointerTo() noexcept = default;
  ALWAYS_INLINE explicit constexpr PythonPointerTo(std::nullptr_t) noexcept {}
  ALWAYS_INLINE PythonPointerTo(PyObject *ptr) noexcept;
  INLINE PythonPointerTo(const PythonPointerTo &copy);
  
  INLINE ~PythonPointerTo();
  
  constexpr bool is_null() const;
  INLINE size_t get_hash() const;
  
  ALWAYS_INLINE void clear();
  
  constexpr PyObject *p() const noexcept;
  
  INLINE PythonPointerTo &operator = (PyObject *ptr);
  INLINE PythonPointerTo &operator = (const PythonPointerTo &copy);

  void output(std::ostream &out) const;

public:
  INLINE PythonPointerTo(PythonPointerTo &&from) noexcept;

  INLINE bool operator < (const PyObject *other) const;
  INLINE bool operator < (const PythonPointerTo &other) const;

  INLINE bool operator == (PyObject *other);
  INLINE bool operator == (const PythonPointerTo &other) const;
  
  INLINE bool operator != (PyObject *other);
  INLINE bool operator != (const PythonPointerTo &other) const;
  
  INLINE PythonPointerTo &operator = (PythonPointerTo &&from) noexcept;
  
  constexpr PyObject &operator *() const noexcept;
  constexpr PyObject *operator -> () const noexcept;
  constexpr operator PyObject *() const noexcept;

  INLINE PyObject *&cheat();

  INLINE void swap(PythonPointerTo &other) noexcept;
  
  ALWAYS_INLINE static PythonPointerTo inplace(PyObject *ptr) noexcept;

protected:
  INLINE void reassign(PyObject *ptr);
  INLINE void reassign(const PythonPointerTo &copy);
  INLINE void reassign(PythonPointerTo &&from) noexcept;

  PyObject *_ptr = nullptr;
};

/*
// The existence of these functions makes it possible to sort vectors of
// PythonPointerTo objects without incurring the cost of unnecessary reference count
// changes.  The performance difference is dramatic!
void swap(PythonPointerTo &one, PythonPointerTo &two) noexcept {
  one.swap(two);
}
*/

// Finally, we'll define a couple of handy abbreviations to save on all that
// wasted typing time.
#define PYPT PythonPointerTo

#include "pythonPointerTo.I"

#endif // HAVE_PYTHON
#endif // PYTHONPOINTERTO_H