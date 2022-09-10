#ifndef CACTOR_EXT_H
#define CACTOR_EXT_H

#include "dtoolbase.h"

#ifdef HAVE_PYTHON

#include "extension.h"
#include "cActor.h"
#include "py_panda.h"

/**
 * This class defines the extension methods for CActor, which are
 * called instead of any C++ methods with the same prototype.
 */
template<>
class Extension<CActor> : public ExtensionBase<CActor> {
public:
  void __init__(PyObject *self, PyObject *models=Py_None, PyObject *anims=Py_None, PyObject *other=Py_None, PyObject *copy=Py_True,
                PyObject *lod_node=Py_None, PyObject *flattenable=Py_True, PyObject *set_final=Py_False, PyObject *ok_missing=Py_None);

  //PyObject *__reduce__(PyObject *self) const;
  
  void load_anims(PyObject *anims=Py_None, PyObject *part_name=Py_None, PyObject *lod_name=Py_None, PyObject *load_now=Py_False);
};

#endif  // HAVE_PYTHON

#endif  // CACTOR_EXT_H
