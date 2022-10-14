#include "cActor_ext.h"

#ifdef HAVE_PYTHON

#define PyString_Check(obj) (PyUnicode_Check(obj) != 0 || PyBytes_Check(obj) != 0)

std::string PyString_ToString(PyObject *obj) {
    char *str = nullptr;
    Py_ssize_t str_len = 0;

    PyObject *bytesObj = nullptr;

    std::string str_cpy;

    // If the passed Python Object is a nullptr or is a None Object, 
    // Just return a empty string.
    if (obj == nullptr || obj == Py_None) { return std::string(""); }

    if (PyUnicode_Check(obj) != 0) {
        bytesObj = PyUnicode_AsASCIIString(obj);
        // Converting the Unicode Object will automatically
        // increase the reference count for us in in the new object.
    } else {
        bytesObj = obj;
        // Increase our reference count to the object so it will not
        // deallocate when we're using it.
        Py_XINCREF(bytesObj);
    }

    int success = PyBytes_AsStringAndSize(bytesObj, &str, &str_len);
    // If we failed to convert the string from a Bytes Object, We'll return a empty string.
    if (success == -1) {
        str_cpy = std::string(""); 
    } else {
        // Create our string copy.
        str_cpy = std::string(str, str_len);
    }

    // Cleanup our Python Objects.
    Py_XDECREF(bytesObj);
    // Return our new string.
    return str_cpy;
}

void Extension<CActor>::__init__(PyObject *self, PyObject *models, PyObject *anims, PyObject *other, PyObject *copy,
                                 PyObject *lod_node, PyObject *flattenable, PyObject *set_final, PyObject *ok_missing) {
    bool _copy = true;
    bool _flattenable = true;
    bool _set_final = false;
    bool _ok_missing = true;

    // Any and all needed types.
    Dtool_TypeMap *tmap = Dtool_GetGlobalTypeMap();
    Dtool_TypeMap::const_iterator it = tmap->find("NodePath");
    Dtool_PyTypedObject *NodePath_py_type = (*it).second;

    // Use _this instead of this.

    // Get all of our boolean variables and decrement the references for
    // the objects we on longer need.
    _copy = PyObject_IsTrue(copy);
    _flattenable = PyObject_IsTrue(flattenable);
    _set_final = PyObject_IsTrue(set_final);
    _ok_missing = (ok_missing != Py_None);


    if (other == Py_None) {
        _this->initialize_geom_node(_flattenable);

        // Load models
        //
        // Four cases:
        //
        //   models, anims{} = Single part actor
        //   models{}, anims{} =  Single part actor w/ LOD
        //   models{}, anims{}{} = Multi-part actor
        //   models{}{}, anims{}{} = Multi-part actor w/ LOD
        //
        // Make sure we have models
        if (PyDict_Check(models) != 0) {
            PyObject *model_key = nullptr, *model_value = nullptr, *anim_key = nullptr, *anim_value = nullptr;
            Py_ssize_t model_pos = 0, anim_pos = 0;

            // Increment our iterators and get the values.
            PyDict_Next(models, &model_pos, &model_key, &model_value);
            if (PyDict_Check(anims) != 0) { PyDict_Next(anims, &anim_pos, &anim_key, &anim_value); }

            // If the model_value isn't a dict object, Then it isn't a multi-part actor w/ LOD.
            // But if it is, We will loop the models dictionary and it's sub dictionaries.
            // If the anim_value isn't a dict object, Then it isn't a multipart actor w/o LOD.
            // In that case, It will be a single part actor w/ LOD.
            if (PyDict_Check(model_value) != 0) {
                // Get and set our lod node from the python object.
                NodePath *lod_node_ptr = nullptr;
                if (lod_node != Py_None && DtoolInstance_GetPointer(lod_node, lod_node_ptr, *NodePath_py_type)) {
                    _this->set_LOD_node(*lod_node_ptr);
                }

                // Preserve numerical order for lod's
                // This will make it easier to set ranges
                PyObject *keys = PyDict_Keys(models);
                Py_XINCREF(keys);

                // Sort our list of keys.
                PyList_Sort(keys);

                // Iterate the list.
                Py_ssize_t key_size = PyList_Size(keys);
                for (Py_ssize_t i = 0; i < key_size; i++) {
                    PyObject *key = PyList_GetItem(keys, i);
                    Py_XINCREF(key);

                    std::string lod_name = PyString_ToString(key);

                    // Make a node under the LOD switch
                    // for each LOD (Just because!)
                    _this->add_LOD(lod_name);

                    PyObject *lod_models = PyDict_GetItem(models, key);
                    Py_XINCREF(lod_models);
                    Py_XDECREF(key);

                    PyObject *lod_model_key, *lod_model_value;
                    Py_ssize_t lod_model_pos = 0;

                    // Iterate over the internal dict
                    while (PyDict_Next(lod_models, &lod_model_pos, &lod_model_key, &lod_model_value)) {
                        std::string model_path = PyString_ToString(lod_model_value);
                        std::string part_name = PyString_ToString(lod_model_key);

                        _this->load_model(model_path, part_name, lod_name, _copy, _ok_missing);
                    }

                    Py_XDECREF(lod_models);
                }

                Py_XDECREF(keys);
            } else if (PyDict_Check(anims) != 0 && PyDict_Check(anim_value) != 0) {
                // Reset the iteration position for our iteration over the models dict.
                model_pos = 0;

                while (PyDict_Next(models, &model_pos, &model_key, &model_value)) {
                    std::string model_path = PyString_ToString(model_value);
                    std::string part_name = PyString_ToString(model_key);

                    _this->load_model(model_path, part_name, "lodRoot", _copy, _ok_missing);
                }
            } else {
                // Get and set our lod node from the python object.
                NodePath *lod_node_ptr = nullptr;
                if (lod_node != Py_None && DtoolInstance_GetPointer(lod_node, lod_node_ptr, *NodePath_py_type)) {
                    _this->set_LOD_node(*lod_node_ptr);
                }

                // Preserve numerical order for lod's
                // This will make it easier to set ranges
                PyObject *keys = PyDict_Keys(models);
                Py_XINCREF(keys);

                // Sort our list of keys.
                PyList_Sort(keys);

                // Iterate the list.
                Py_ssize_t key_size = PyList_Size(keys);
                for (Py_ssize_t i = 0; i < key_size; i++) {
                    PyObject *key = PyList_GetItem(keys, i);
                    Py_XINCREF(key);

                    std::string lod_name = PyString_ToString(key);

                    // Make a node under the LOD switch
                    // for each LOD (Just because!)
                    _this->add_LOD(lod_name);

                    PyObject *model_value = PyDict_GetItem(models, key);
                    Py_XINCREF(model_value);
                    Py_XDECREF(key);

                    _this->load_model(PyString_ToString(model_value), "modelRoot", lod_name, _copy, _ok_missing);

                    Py_XDECREF(model_value);
                }

                Py_XDECREF(keys);
            }
        } else if (PyString_Check(models) != 0) {
            std::string models_str = PyString_ToString(models);

            _this->load_model(models_str, "modelRoot", "lodRoot", _copy, _ok_missing);
        } else if (models != Py_None && DtoolInstance_Check(models) && DtoolInstance_TYPE(models) == NodePath_py_type) {
            NodePath *model_node_ptr = nullptr;
            if (!DtoolInstance_GetPointer(models, model_node_ptr, *NodePath_py_type)) { return; }
                
            _this->load_model(*model_node_ptr, "modelRoot", "lodRoot", _copy, _ok_missing);
        } else if (models != Py_None) {
            std::ostringstream stream;
            stream << "models paramater passed to CActor constructor must be a dict, str, or NodePath";
            std::string str = stream.str();
            PyErr_SetString(PyExc_TypeError, str.c_str());
            return;
        }

        // Make sure the Actor has animations.
        if (PyDict_Check(anims) != 0 && PyDict_Size(anims) >= 1) {
            PyObject *model_key = nullptr, *model_value = nullptr, *anim_key = nullptr, *anim_value = nullptr;
            Py_ssize_t model_pos = 0, anim_pos = 0;

            // Increment our iterators and get the values.
            if (PyDict_Check(models) != 0) { PyDict_Next(models, &model_pos, &model_key, &model_value); }
            PyDict_Next(anims, &anim_pos, &anim_key, &anim_value);

            if (PyDict_Check(anim_value) != 0) {
                // Are the models a dict of dicts too?
                if (PyDict_Check(models) != 0 && PyDict_Check(model_value) != 0) {
                    // Then we have a multi-part w/ LOD

                    // Preserve numerical order for lod's
                    // This will make it easier to set ranges
                    PyObject *keys = PyDict_Keys(models);
                    Py_XINCREF(keys);

                    // Sort our list of keys.
                    PyList_Sort(keys);

                    // Iterate the list.
                    Py_ssize_t key_size = PyList_Size(keys);
                    for (Py_ssize_t i = 0; i < key_size; i++) {
                        PyObject *key = PyList_GetItem(keys, i);
                        Py_XINCREF(key);

                        std::string lod_name = PyString_ToString(key);
                        Py_XDECREF(key);

                        // Reset the animation iteration position to parse from the start.
                        anim_pos = 0;

                        // Iterate over both dicts
                        while (PyDict_Next(anims, &anim_pos, &anim_key, &anim_value)) {
                            pvector<std::pair<std::string, std::string> > anims;

                            // Get the part name from our animation key.
                            std::string part_name = PyString_ToString(anim_key);

                            PyObject *anim_info_key = nullptr, *anim_info_value = nullptr;
                            Py_ssize_t anim_info_pos = 0;

                            // Read out all of the animations into the vector we have set up.
                            while (PyDict_Next(anim_value, &anim_info_pos, &anim_info_key, &anim_info_value)) {
                                std::string anim_name = PyString_ToString(anim_info_key);
                                std::string anim_filename = PyString_ToString(anim_info_value);

                                anims.emplace_back(std::make_pair(anim_name, anim_filename));
                            }

                            _this->load_anims(anims, part_name, lod_name);
                        }
                    }

                    Py_XDECREF(keys);
                } else {
                    // Then it must be multi-part w/o LOD

                    // Reset the animation iteration position to parse from the start.
                    anim_pos = 0;

                    // Iterate over both dicts
                    while (PyDict_Next(anims, &anim_pos, &anim_key, &anim_value)) {
                        pvector<std::pair<std::string, std::string> > anims;

                        // Get the part name from our animation key.
                        std::string part_name = PyString_ToString(anim_key);

                        PyObject *anim_info_key = nullptr, *anim_info_value = nullptr;
                        Py_ssize_t anim_info_pos = 0;

                        // Read out all of the animations into the vector we have set up.
                        while (PyDict_Next(anim_value, &anim_info_pos, &anim_info_key, &anim_info_value)) {
                            std::string anim_name = PyString_ToString(anim_info_key);
                            std::string anim_filename = PyString_ToString(anim_info_value);

                            anims.emplace_back(std::make_pair(anim_name, anim_filename));
                        }

                        _this->load_anims(anims, part_name, "lodRoot");
                    }
                }
            } else if (PyDict_Check(models) != 0) {
                // We have single-part w/ LOD

                // Preserve numerical order for lod's
                // This will make it easier to set ranges
                PyObject *keys = PyDict_Keys(models);
                Py_XINCREF(keys);

                // Sort our list of keys.
                PyList_Sort(keys);

                // Iterate the list.
                Py_ssize_t key_size = PyList_Size(keys);
                for (Py_ssize_t i = 0; i < key_size; i++) {
                    pvector<std::pair<std::string, std::string> > anims;

                    PyObject *key = PyList_GetItem(keys, i);
                    Py_XINCREF(key);

                    std::string lod_name = PyString_ToString(key);
                    Py_XDECREF(key);

                    PyObject *anim_info_key = nullptr, *anim_info_value = nullptr;
                    Py_ssize_t anim_info_pos = 0;

                    // Read out all of the animations into the vector we have set up.
                    while (PyDict_Next(anim_value, &anim_info_pos, &anim_info_key, &anim_info_value)) {
                        std::string anim_name = PyString_ToString(anim_info_key);
                        std::string anim_filename = PyString_ToString(anim_info_value);

                        anims.emplace_back(std::make_pair(anim_name, anim_filename));
                    }

                    _this->load_anims(anims, "modelRoot", lod_name);
                }

                Py_XDECREF(keys);
            } else {
                // Otherwise it is single-part w/o LOD

                pvector<std::pair<std::string, std::string> > anims;

                PyObject *anim_info_key = nullptr, *anim_info_value = nullptr;
                Py_ssize_t anim_info_pos = 0;

                // Read out all of the animations into the vector we have set up.
                while (PyDict_Next(anim_value, &anim_info_pos, &anim_info_key, &anim_info_value)) {
                    std::string anim_name = PyString_ToString(anim_info_key);
                    std::string anim_filename = PyString_ToString(anim_info_value);

                    anims.emplace_back(std::make_pair(anim_name, anim_filename));
                }

                _this->load_anims(anims, "modelRoot", "lodRoot");
            }
        }
    } else {
        // Get our CActor type.
        it = tmap->find("CActor");
        Dtool_PyTypedObject *CActor_py_type = (*it).second;

        if (CActor_py_type == nullptr) { return; }

        // Get and set our CActor from the python object.
        CActor *other_ptr = NULL;
        if (!DtoolInstance_GetPointer(other, other_ptr, *CActor_py_type)) { return; }

        *_this = *other_ptr;
    }

    if (_set_final) {
        // If setFinal is true, the Actor will set its top bounding
        // volume to be the "final" bounding volume: the bounding
        // volumes below the top volume will not be tested.  If a
        // cull test passes the top bounding volume, the whole
        // Actor is rendered.

        // We do this partly because an Actor is likely to be a
        // fairly small object relative to the scene, and is pretty
        // much going to be all onscreen or all offscreen anyway;
        // and partly because of the Character bug that doesn't
        // update the bounding volume for pieces that animate away
        // from their original position.  It's disturbing to see
        // someone's hands disappear; better to cull the whole
        // object or none of it.
        _this->_geom_node.node()->set_final(true);
    }
}


void Extension<CActor>::load_anims(PyObject *anims, PyObject *part_name, PyObject *lod_name, PyObject *load_now) {
    bool _load_now = false;
    std::string _part_name("modelRoot");
    std::string _lod_name("lodRoot");
    pvector<std::pair<std::string, std::string> > _anims;

    _load_now = PyObject_IsTrue(load_now);

    if (PyString_Check(part_name)) { _part_name = PyString_ToString(part_name); }
    if (PyString_Check(lod_name)) { _lod_name = PyString_ToString(lod_name); }

    if (PyDict_Check(anims) != 0) {
        PyObject *anim_key = nullptr, *anim_value = nullptr;
        Py_ssize_t anim_pos = 0;
        
        // Read out all of the animations into the vector we have set up.
        while (PyDict_Next(anims, &anim_pos, &anim_key, &anim_value)) {
            std::string anim_name = PyString_ToString(anim_key);
            std::string anim_filename = PyString_ToString(anim_value);
            
            _anims.emplace_back(std::make_pair(anim_name, anim_filename));
        }
    }

    _this->load_anims(_anims, _part_name, _lod_name, _load_now);
}

void Extension<CActor>::set_play_rate(PyObject *rate, PyObject *anim, PyObject *part_name, PyObject *layer) {
    PN_stdfloat _rate = 1.0;
    std::string _part_name("modelRoot");
    std::string _anim_name("");
    int _layer = 0;
        
    // The play rate is a required paramater.
    if (rate == nullptr || rate == Py_None || !PyFloat_Check(rate)) {
        std::ostringstream stream;
        stream << "rate paramater passed to set_play_rate is required and must be a float!";
        std::string str = stream.str();
        PyErr_SetString(PyExc_TypeError, str.c_str());
        return; 
    }
    
    // Get our play rate.
    _rate = (PN_stdfloat)PyFloat_AsDouble(rate);
    
    // Check if our animation name is valid for use, If so. Extract it from the PyObject.
    if (PyString_Check(anim)) { _anim_name = PyString_ToString(anim); }
    
    // Check if our part name is valid for use, If so. Extract it from the PyObject.
    if (PyString_Check(part_name)) { _part_name = PyString_ToString(part_name); }
    
    // Check if our layer is valid for use, If so. Extract it from the PyObject.
    if (PyLong_Check(layer)) { _layer = PyLong_AsLong(layer); }
    
    // Now we set our own play rate.
    _this->set_play_rate(_rate, _anim_name, _part_name, _layer);
}

PyObject *Extension<CActor>::get_LOD_names() {
    // Get all of our lod names.
    pvector<std::string> lod_names = _this->get_LOD_names();

    // Create our list to append the string objects to.
    PyObject *lod_name_list = PyList_New(0);

    for (size_t i = 0; i < lod_names.size(); i++) {
        std::string lod_name = lod_names[i];

        // Create a unicode string object from the string.
        PyObject *str_object = PyUnicode_FromStringAndSize(lod_name.data(), lod_name.size());
        if (str_object == nullptr) { continue; }

        // Add the string item to our list.
        int error = PyList_Append(lod_name_list, str_object);
    }

    return lod_name_list;
}

PyObject *Extension<CActor>::get_anim_defs(PyObject *anim, PyObject *parts, PyObject *lod) {
    long long anim_index = -1;
    std::string anim_name;
    std::string lod_name("lodRoot");
    std::vector<CActor::AnimDef> anim_defs;
    
    // Any and all needed types for constructing PyObjects or extracting pointers from them.
    Dtool_TypeMap *tmap = Dtool_GetGlobalTypeMap();
    Dtool_TypeMap::const_iterator it = tmap->find("CActor::AnimDef");
    Dtool_PyTypedObject *AnimDef_py_type = (*it).second;
    if (AnimDef_py_type == nullptr) {
        std::ostringstream stream;
        stream << "Failed to get dtool type for CActor::AnimDef!";
        std::string str = stream.str();
        PyErr_SetString(PyExc_LookupError, str.c_str());
        return Py_None;
    }
    
    // Create our list to append the animation definitions to.
    PyObject *anim_def_list = PyList_New(0);
    
    // Convert our anim argument.
    if (PyString_Check(anim)) {
        anim_name = PyString_ToString(anim);
    } else if (PyLong_Check(anim)) {
        anim_index = PyLong_AsLongLong(anim);
    } else {
        std::ostringstream stream;
        stream << "anim paramater passed to get_anim_defs() must be a str or int.";
        std::string str = stream.str();
        PyErr_SetString(PyExc_TypeError, str.c_str());
        return anim_def_list;
    }
    
    // Convert our lod argument if one was given.
    if (PyString_Check(lod)) { // We do have a specified LOD to use, And it's a string!
        lod_name = PyString_ToString(lod);
    } else if (lod != Py_None) { // We have a specified LOD to use, But isn't a string.
        std::ostringstream stream;
        stream << "lod paramater passed to get_anim_defs() must be a str or None.";
        std::string str = stream.str();
        PyErr_SetString(PyExc_TypeError, str.c_str());
        return anim_def_list;
    }
    
    // Convert our parts argument if one was given.
    // And then get the animation definitions.
    if (parts == Py_None) { // We want all parts to be used.
        if (!anim_name.empty()) {
            anim_defs = _this->get_anim_defs(anim_name);
        } else {
            anim_defs = _this->get_anim_defs(anim_index);
        }
    } else if (PyList_Check(parts)) { // We have a list of parts to use.
        // Get our lists size.
        Py_ssize_t parts_size = PyList_Size(parts);
        
        // Pre-reserve the space needed for our part names.
        pvector<std::string> part_names;
        part_names.reserve(parts_size);
        
        // Iterate the list.
        for (Py_ssize_t i = 0; i < parts_size; i++) {
            PyObject *part = PyList_GetItem(parts, i);
            Py_XINCREF(part);

            std::string part_name = PyString_ToString(part);
            Py_XDECREF(part);

            part_names.emplace_back(part_name);
        }
        
        if (!anim_name.empty()) {
            anim_defs = _this->get_anim_defs(anim_name, part_names, lod_name);
        } else {
            anim_defs = _this->get_anim_defs(anim_index, part_names, lod_name);
        }
    } else if (PyString_Check(parts)) { // We have a particular part to use.
        std::string part_name = PyString_ToString(parts);
        
        if (!anim_name.empty()) {
            anim_defs = _this->get_anim_defs(anim_name, part_name, lod_name);
        } else {
            anim_defs = _this->get_anim_defs(anim_index, part_name, lod_name);
        }
    } else { // We have a invalid type passed as a part.
        std::ostringstream stream;
        stream << "parts paramater passed to get_anim_defs() must be a str, list (of strings), or None.";
        std::string str = stream.str();
        PyErr_SetString(PyExc_TypeError, str.c_str());
        return anim_def_list;
    }
    
    // Convert all of our AnimDefs into PyObjects to return in our list.
    for (size_t i = 0; i < anim_defs.size(); i++) {
        CActor::AnimDef &anim_def = anim_defs[i];
        
        // Copy the animation definition.
        CActor::AnimDef *anim_def_copy = new CActor::AnimDef(anim_def);
        
        // Create the Python Instance for our animation definition.
        PyObject *anim_def_obj = DTool_CreatePyInstanceTyped(anim_def_copy, *AnimDef_py_type, true, false, anim_def.as_typed_object()->get_type_index());
        if (anim_def_obj == nullptr) { 
            // Free the copy we made which failed to be bound to a PyObject.
            delete anim_def_copy;
            continue; 
        }
        
        // Add the animation definition to our list.
        int error = PyList_Append(anim_def_list, anim_def_obj);
    }
    
    return anim_def_list;
}

PyObject *Extension<CActor>::get_part_bundle_dict() {
    // Any and all needed types for constructing PyObjects or extracting pointers from them.
    Dtool_TypeMap *tmap = Dtool_GetGlobalTypeMap();
    Dtool_TypeMap::const_iterator it = tmap->find("CActor::PartDef");
    Dtool_PyTypedObject *PartDef_py_type = (*it).second;
    if (PartDef_py_type == nullptr) {
        std::ostringstream stream;
        stream << "Failed to get dtool type for CActor::PartDef!";
        std::string str = stream.str();
        PyErr_SetString(PyExc_LookupError, str.c_str());
        return Py_None;
    }
    
    PyObject *py_part_bundle_dict = PyDict_New();
    // If we fail to create the dict, Just return a None object.
    if (py_part_bundle_dict == nullptr) { return Py_None; }
    
    // Get our part bundle dict.
    const CActor::PartBundleDict &part_bundle_dict = _this->get_part_bundle_dict();
    
    // Parse through our part bundle dict and convert it to a PyObject dict.
    for (CActor::PartBundleDict::const_iterator it = part_bundle_dict.begin(); it != part_bundle_dict.end(); it++) {
        std::string curr_lod_name, curr_part_name;
        std::string bundle_name(it->first);
        const CActor::PartDef &part_def = it->second;
        
        // Get back both our lod name and our part name by splitting the string.
        curr_lod_name = bundle_name.substr(0, bundle_name.find(':'));
        // Erase the lod name and the delimiter.
        bundle_name.erase(0, bundle_name.find(':') + 1);
        // The bundle name is now the part name.
        curr_part_name = std::move(bundle_name);
        
        // Create a unicode string objects from the strings.
        PyObject *curr_lod_name_object = PyUnicode_FromStringAndSize(curr_lod_name.data(), curr_lod_name.size());
        if (curr_lod_name_object == nullptr) { continue; }
        
        PyObject *curr_part_name_object = PyUnicode_FromStringAndSize(curr_part_name.data(), curr_part_name.size());
        if (curr_part_name_object == nullptr) { continue; }
        
        // Get or create the internal dict the LOD we're using.
        PyObject *py_part_bundle_dict_lod = nullptr;
        if (PyDict_Contains(py_part_bundle_dict, curr_lod_name_object) == 0) {
            py_part_bundle_dict_lod = PyDict_New();
            // If we fail to create the dict, Just return a None object.
            if (py_part_bundle_dict_lod == nullptr) { return Py_None; }
            
            int error = PyDict_SetItem(py_part_bundle_dict, curr_lod_name_object, py_part_bundle_dict_lod);
            if (error == -1) { return Py_None; }
        } else {
            py_part_bundle_dict_lod = PyDict_GetItemWithError(py_part_bundle_dict, curr_lod_name_object);
            if (py_part_bundle_dict_lod == nullptr) { return Py_None; }
        }
        // Increment the reference so we don't lose it.
        Py_XINCREF(py_part_bundle_dict_lod);
        
        // Copy the part definition.
        CActor::PartDef *part_def_copy = new CActor::PartDef(part_def);
        
        // Create the Python Instance for our part definition.
        PyObject *part_def_obj = DTool_CreatePyInstanceTyped(part_def_copy, *PartDef_py_type, true, false, part_def.as_typed_object()->get_type_index());
        if (part_def_obj == nullptr) {
            // Free the copy we made which failed to be bound to a PyObject.
            delete part_def_copy;
            // Decrement the reference, We no longer need it.
            Py_XDECREF(py_part_bundle_dict_lod);
            continue; 
        }
        
        // Add the PartDef object to the LOD dictonary.
        int error = PyDict_SetItem(py_part_bundle_dict_lod, curr_part_name_object, part_def_obj);
        // Decrement the reference before we do the error check.
        Py_XDECREF(py_part_bundle_dict_lod);
        // Handle the error.
        if (error == -1) { continue; }
    }
    
    return py_part_bundle_dict;
}

#endif // HAVE_PYTHON