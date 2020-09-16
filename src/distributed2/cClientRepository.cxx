/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file cClientRepository.cxx
 * @author lachbr
 * @date 2020-09-15
 */

#include "cClientRepository.h"
#include "dcClass.h"
#include "dcField.h"
#include "dcParameter.h"
#include "dcPacker.h"
#include "extension.h"

void CClientRepository::
unpack_server_snapshot(DatagramIterator &dgi) {
  bool is_delta = (bool)dgi.get_uint8();
  int num_objects = dgi.get_uint16();

  PyMutexHolder holder;

  PyObject *doid2do = PyObject_GetAttrString(_py_repo, (char *)"doId2do");
  if (!doid2do) {
    PyErr_Print();
    return;
  }

  std::cout << num_objects << " objects" << std::endl;

  for (int i = 0; i < num_objects; i++) {
    DOID_TYPE do_id = dgi.get_uint32();
    std::cout << "doid " << do_id << std::endl;

    PyObject *py_do_id = PyLong_FromUnsignedLong(do_id);
    PyObject *dist_obj = PyDict_GetItem(doid2do, py_do_id);

    Py_DECREF(py_do_id);

    if (!dist_obj) {
      std::ostringstream ss;
      ss << "Received state snapshot for object id " << do_id << ", but not found in doId2do";
      std::string message = ss.str();
      PyErr_SetString(PyExc_KeyError, message.c_str());
      return;
    }

    PyObject *py_dclass = PyObject_GetAttrString(dist_obj, (char *)"dclass");
    if (!py_dclass) {
      PyErr_Print();
      return;
    }

    PyObject *py_dclass_this = PyObject_GetAttrString(py_dclass, (char *)"this");
    Py_DECREF(py_dclass);
    if (!py_dclass_this) {
      PyErr_Print();
      return;
    }

    DCClass *dclass = (DCClass *)PyLong_AsVoidPtr(py_dclass_this);
    Py_DECREF(py_dclass_this);

    if (!unpack_object_state(dgi, dist_obj, dclass, do_id)) {
      return;
    }
  }

  Py_DECREF(doid2do);
}

bool CClientRepository::
unpack_object_state(DatagramIterator &dgi, PyObject *dist_obj, DCClass *dclass,
                    DOID_TYPE do_id) {
  int num_fields = dgi.get_uint16();

  char proxy_name[256];
  DCPacker packer;

  const char *data = (const char *)dgi.get_datagram().get_data();

  for (int j = 0; j < num_fields; j++) {
    int field_number = dgi.get_uint16();

    DCField *field = dclass->get_inherited_field(field_number);
    if (!field) {
      std::ostringstream ss;
      ss << "Inherited field " << field_number << " not found on " << do_id;
      std::string message = ss.str();
      PyErr_SetString(PyExc_AttributeError, message.c_str());
      return false;
    }

    DCParameter *param = field->as_parameter();
    if (!param) {
      std::ostringstream ss;
      ss << "Inherited field " << field_number << " on " << do_id << " is not a parameter";
      std::string message = ss.str();
      PyErr_SetString(PyExc_AttributeError, message.c_str());
      return false;
    }

    const char *c_name = field->get_name().c_str();

    std::cout << "field " << field->get_name() << std::endl;

    // Put the buffer in the DCPacker to unpack the data into python objects
    packer.set_unpack_data(data + dgi.get_current_index(), dgi.get_remaining_size(), false);
    packer.begin_unpack(field);
    PyObject *args = invoke_extension(field).unpack_args(packer);
    packer.end_unpack();

    // Skip over the bytes in the DGI that the DCPacker just unpacked
    dgi.skip_bytes(packer.get_num_unpacked_bytes());

    if (!args) {
      std::ostringstream ss;
      ss << "Unable to unpack inherited field " << field_number << " on object " << do_id;
      std::string message = ss.str();
      PyErr_SetString(PyExc_BufferError, message.c_str());
      return false;
    }

    // Now set the args on the field
    sprintf(proxy_name, "RecvProxy_%s", c_name);
    if (PyObject_HasAttrString(dist_obj, proxy_name)) {
      // If we have a proxy for this field, allow the proxy method to
      // do whatever it needs to do with the args
      PyObject *proxy = PyObject_GetAttrString(dist_obj, proxy_name);

      if (PyTuple_Check(args)) {
        // Args are already a tuple
        PyObject_CallObject(proxy, args);

      } else {
        // The arguments are not already a tuple. Since we are calling a
        // method, the arguments need to be in a tuple.
        PyObject *tuple_args = PyTuple_Pack(1, args);
        PyObject_CallObject(proxy, tuple_args);
        Py_DECREF(tuple_args);
      }

      Py_DECREF(proxy);

    } else {
      // Set the args directly on the attribute on the object with the
      // name of the field.
      PyObject_SetAttrString(dist_obj, c_name, args);
    }

    Py_DECREF(args);
  }

  return true;
}
