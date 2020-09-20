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

/**
 * Unpacks a server snapshot from the datagram and applies the state onto the
 * distributed objects.
 */
void CClientRepository::
unpack_server_snapshot(DatagramIterator &dgi) {
  bool is_delta = (bool)dgi.get_uint8();
  int num_objects = dgi.get_uint16();

  if (distributed2_cat.is_debug()) {
    distributed2_cat.debug()
      << "Unpacking " << num_objects << " objects in snapshot\n";
  }

  PyMutexHolder holder;

  PyObject *doid2do = PyObject_GetAttrString(_py_repo, (char *)"doId2do");
  if (!doid2do) {
    PyErr_Print();
    return;
  }

  for (int i = 0; i < num_objects; i++) {
    DOID_TYPE do_id = dgi.get_uint32();

    PyObject *py_do_id = PyLong_FromUnsignedLong(do_id);
    PyObject *dist_obj = PyDict_GetItem(doid2do, py_do_id);

    Py_DECREF(py_do_id);

    if (!dist_obj) {
      std::ostringstream ss;
      ss << "Received state snapshot for object id " << do_id << ", but not found in doId2do";
      std::string message = ss.str();
      PyErr_SetString(PyExc_KeyError, message.c_str());
      Py_DECREF(doid2do);
      return;
    }

    PyObject *py_dclass = PyObject_GetAttrString(dist_obj, (char *)"dclass");
    if (!py_dclass) {
      PyErr_Print();
      Py_DECREF(doid2do);
      return;
    }

    PyObject *py_dclass_this = PyObject_GetAttrString(py_dclass, (char *)"this");
    Py_DECREF(py_dclass);
    if (!py_dclass_this) {
      PyErr_Print();
      Py_DECREF(doid2do);
      return;
    }

    DCClass *dclass = (DCClass *)PyLong_AsVoidPtr(py_dclass_this);
    Py_DECREF(py_dclass_this);

    if (!unpack_object_state(dgi, dist_obj, dclass, do_id)) {
      Py_DECREF(doid2do);
      return;
    }
  }

  Py_DECREF(doid2do);
}

/**
 * Unpacks the object state from the datagram and applies it to the specified
 * distributed object.
 */
bool CClientRepository::
unpack_object_state(DatagramIterator &dgi, PyObject *dist_obj, DCClass *dclass,
                    DOID_TYPE do_id) {

  // First call the preDataUpdate method on the object so they can do stuff
  // before we unpack the state.
  PyObject *pre_data_update = PyObject_GetAttrString(dist_obj, (char *)"preDataUpdate");
  if (pre_data_update) {
    PyObject_CallObject(pre_data_update, NULL);
    Py_DECREF(pre_data_update);
  }

  int num_fields = dgi.get_uint16();

  if (distributed2_cat.is_debug()) {
    distributed2_cat.debug()
      << "Unpacking " << num_fields << " fields on object " << do_id << "\n";
  }

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

    if (distributed2_cat.is_debug()) {
      distributed2_cat.debug()
        << "Unpacking field " << field_number << " (" << field->get_name() << ") on "
        << do_id << "\n";
    }

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

      if (distributed2_cat.is_debug()) {
        distributed2_cat.debug()
          << "Calling recv proxy\n";
      }

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
      if (distributed2_cat.is_debug()) {
        distributed2_cat.debug()
          << "Setting unpacked value directly on object\n";
      }
      PyObject_SetAttrString(dist_obj, c_name, args);
    }

    // Check to see if the object defines a method to handle when this
    // particuler field is unpacked.
    // Re-use the proxy_name buffer
    sprintf(proxy_name, "OnRecv_%s", c_name);
    if (PyObject_HasAttrString(dist_obj, proxy_name)) {
      // Call it
      PyObject *recv_handler = PyObject_GetAttrString(dist_obj, proxy_name);
      PyObject_CallObject(recv_handler, NULL);
      Py_DECREF(recv_handler);
    }

    Py_DECREF(args);
  }

  // Finally call the postDataUpdate method so they can do stuff after we've
  // unpacked the state.
  PyObject *post_data_update = PyObject_GetAttrString(dist_obj, (char *)"postDataUpdate");
  if (post_data_update) {
    PyObject_CallObject(post_data_update, NULL);
    Py_DECREF(post_data_update);
  }

  return true;
}
