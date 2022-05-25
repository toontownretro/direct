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
#include "dcField_ext.h"
#include "dcParameter.h"
#include "dcPacker.h"
#include "extension.h"
#include "pStatCollector.h"
#include "pStatTimer.h"

static PStatCollector unpack_snapshot_coll("App:CClientRepository:UnpackSnapshot");
static PStatCollector unpack_object_coll("App:CClientRepository:UnpackSnapshot:UnpackObject");
static PStatCollector find_in_map_coll("App:CClientRepository:UnpackSnapshot:UnpackObject:FindInTable");
static PStatCollector pre_data_coll("App:CClientRepository:UnpackSnapshot:UnpackObject:PreDataUpdate");
static PStatCollector unpack_args_coll("App:CClientRepository:UnpackSnapshot:UnpackObject:UnpackFieldArgs");
static PStatCollector recv_proxy_coll("App:CClientRepository:UnpackSnapshot:UnpackObject:ReceiveProxy");
static PStatCollector set_field_coll("App:CClientRepository:UnpackSnapshot:UnpackObject:SetField");
static PStatCollector post_data_coll("App:CClientRepository:UnpackSnapshot:UnpackObject:PostDataUpdate");

/**
 * Unpacks a server snapshot from the datagram and applies the state onto the
 * distributed objects.
 */
void CClientRepository::
unpack_server_snapshot(DatagramIterator &dgi, bool is_delta) {
  PStatTimer timer(unpack_snapshot_coll);

  int num_objects = dgi.get_uint16();

  if (distributed2_cat.is_debug()) {
    distributed2_cat.debug()
      << "Unpacking " << num_objects << " objects in snapshot\n";
  }

  PyMutexHolder holder;

  for (int i = 0; i < num_objects; i++) {
    DOID_TYPE do_id = dgi.get_uint32();
    if (!unpack_object_state(dgi, do_id)) {
      return;
    }
  }
}

/**
 * Unpacks the object state from the datagram and applies it to the specified
 * distributed object.
 */
bool CClientRepository::
unpack_object_state(DatagramIterator &dgi, DOID_TYPE do_id) {

  PStatTimer timer(unpack_object_coll);

  // Find the object in our internal object cache.
  find_in_map_coll.start();
  DODataMap::const_iterator dit = _do_data.find(do_id);
  if (dit == _do_data.end()) {
    distributed2_cat.error()
      << "dist obj " << do_id << " does not exist in CClientRepository object "
      << "table\n";
    find_in_map_coll.stop();
    return false;
  }

  DOData *odata = (*dit).second;

  find_in_map_coll.stop();

  PyObject *dist_obj = odata->_dist_obj;
  DCClass *dclass = odata->_dclass;

  // First call the preDataUpdate method on the object so they can do stuff
  // before we unpack the state.
  if (odata->_pre_data_update != nullptr) {
    pre_data_coll.start();
    PyObject_CallNoArgs(odata->_pre_data_update);
    if (PyErr_Occurred()) {
      distributed2_cat.error()
        << "Python error occurred during preDataUpdate()\n";
      PyErr_Print();
    }
    pre_data_coll.stop();
  }

  int num_fields = dgi.get_uint16();

  if (distributed2_cat.is_debug()) {
    distributed2_cat.debug()
      << "Unpacking " << num_fields << " fields on object " << do_id << "\n";
  }

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

    DOFieldData &field_data = odata->_field_data[field_number];

    if (distributed2_cat.is_debug()) {
      distributed2_cat.debug()
        << "Unpacking field " << field_number << " (" << field->get_name() << ") on "
        << do_id << "\n";
    }

    // Put the buffer in the DCPacker to unpack the data into python objects
    packer.set_unpack_data(data + dgi.get_current_index(), dgi.get_remaining_size(), false);
    packer.begin_unpack(field);
    unpack_args_coll.start();
    PyObject *args = invoke_extension(field).unpack_args(packer);
    unpack_args_coll.stop();
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
    if (field_data._recv_proxy != nullptr) {
      // If we have a proxy for this field, allow the proxy method to
      // do whatever it needs to do with the args

      recv_proxy_coll.start();

      if (distributed2_cat.is_debug()) {
        distributed2_cat.debug()
          << "Calling recv proxy\n";
      }

      if (PyTuple_Check(args)) {
        // Args are already a tuple
        PyObject_CallObject(field_data._recv_proxy, args);
        if (PyErr_Occurred()) {
          distributed2_cat.error()
            << "Python error occurred during recv proxy for field" << field->get_name() << "\n";
          PyErr_Print();
        }

      } else {
        // The arguments are not already a tuple. Since we are calling a
        // method, the arguments need to be in a tuple.
        PyObject *tuple_args = PyTuple_Pack(1, args);
        PyObject_CallObject(field_data._recv_proxy, tuple_args);
        if (PyErr_Occurred()) {
          distributed2_cat.error()
            << "Python error occurred during recv proxy for field" << field->get_name() << "\n";
          PyErr_Print();
        }
        Py_DECREF(tuple_args);
      }

      recv_proxy_coll.stop();

    } else {
      set_field_coll.start();
      // Set the args directly on the attribute on the object with the
      // name of the field.
      if (distributed2_cat.is_debug()) {
        distributed2_cat.debug()
          << "Setting unpacked value directly on object\n";
      }
      PyObject_SetAttr(dist_obj, field_data._field_name, args);
      set_field_coll.stop();
    }

    Py_DECREF(args);
  }

  // Finally call the postDataUpdate method so they can do stuff after we've
  // unpacked the state.
  if (odata->_post_data_update != nullptr) {
    post_data_coll.start();
    PyObject_CallNoArgs(odata->_post_data_update);
    if (PyErr_Occurred()) {
      distributed2_cat.error()
        << "Python error occurred during postDataUpdate()\n";
      PyErr_Print();
    }
    post_data_coll.stop();
  }

  return true;
}

/**
 * Adds the indicated distributed object into the repository's cache.
 */
void CClientRepository::
add_object(PyObject *dist_obj) {
  // Cache off various object attributes, such as the doId, preDataUpdate
  // method, and field receive proxies.  This lets us avoid calling
  // PyObject_GetAttrString each time we unpack a snapshot for the object.

  PyObject *py_do_id = PyObject_GetAttrString(dist_obj, (char *)"doId");
  if (!py_do_id) {
    distributed2_cat.error()
      << "add_object: dist_obj does not have a doId member\n";
    return;
  }

  DOID_TYPE do_id = PyLong_AsUnsignedLong(py_do_id);
  Py_DECREF(py_do_id);

  PyObject *py_dclass = PyObject_GetAttrString(dist_obj, (char *)"dclass");
  if (!py_dclass) {
    distributed2_cat.error()
      << "add_object: dist_obj does not have a dclass member\n";
    return;
  }

  PyObject *py_dclass_this = PyObject_GetAttrString(py_dclass, (char *)"this");
  Py_DECREF(py_dclass);
  if (!py_dclass_this) {
    return;
  }

  DCClass *dclass = (DCClass *)PyLong_AsVoidPtr(py_dclass_this);
  Py_DECREF(py_dclass_this);

  if (dclass == nullptr) {
    distributed2_cat.error()
      << "add_object: invalid dclass\n";
    return;
  }

  PT(DOData) data = new DOData;
  data->_do_id = do_id;
  data->_dclass = dclass;
  data->_dist_obj = dist_obj;
  if (PyObject_HasAttrString(dist_obj, (char *)"preDataUpdate")) {
    data->_pre_data_update = PyObject_GetAttrString(dist_obj, (char *)"preDataUpdate");
  } else {
    data->_pre_data_update = nullptr;
  }
  if (PyObject_HasAttrString(dist_obj, (char *)"postDataUpdate")) {
    data->_post_data_update = PyObject_GetAttrString(dist_obj, (char *)"postDataUpdate");
  } else {
    data->_post_data_update = nullptr;
  }
  data->_on_data_changed = nullptr;

  data->_field_data.resize(dclass->get_num_inherited_fields());

  char proxy_name[256];
  for (size_t i = 0; i < dclass->get_num_inherited_fields(); i++) {
    // Check for proxies on the field.
    DOFieldData &field_data = data->_field_data[i];

    DCField *field = dclass->get_inherited_field(i);
    if (field->as_parameter() == nullptr) {
      continue;
    }
    const char *c_field_name = field->get_name().c_str();

    sprintf(proxy_name, "RecvProxy_%s", c_field_name);
    if (PyObject_HasAttrString(dist_obj, proxy_name)) {
      field_data._recv_proxy = PyObject_GetAttrString(dist_obj, proxy_name);
    } else {
      field_data._recv_proxy = nullptr;
    }

    field_data._field_name = PyUnicode_FromString(c_field_name);
  }

  Py_INCREF(dist_obj);

  _do_data[do_id] = data;
}

/**
 * Removes the distributed object with the indicated DO ID repository's object
 * table.
 */
void CClientRepository::
remove_object(DOID_TYPE do_id) {
  auto it = _do_data.find(do_id);
  if (it == _do_data.end()) {
    return;
  }

  DOData *data = (*it).second;
  Py_XDECREF(data->_dist_obj);
  Py_XDECREF(data->_pre_data_update);
  Py_XDECREF(data->_post_data_update);
  Py_XDECREF(data->_on_data_changed);
  for (size_t i = 0; i < data->_field_data.size(); i++) {
    DOFieldData &fdata = data->_field_data[i];
    Py_XDECREF(fdata._recv_proxy);
    Py_XDECREF(fdata._field_name);
  }

  _do_data.erase(it);
}
