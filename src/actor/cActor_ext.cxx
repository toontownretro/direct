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
            PyObject *model_key, *model_value, *anim_key, *anim_value;
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
                NodePath *lod_node_ptr = NULL;
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
                NodePath *lod_node_ptr = NULL;
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
            NodePath *model_node_ptr = NULL;
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
            PyObject *model_key, *model_value, *anim_key, *anim_value;
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
                            
                            PyObject *anim_info_key, *anim_info_value;
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
                        
                        PyObject *anim_info_key, *anim_info_value;
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
                    
                    PyObject *anim_info_key, *anim_info_value;
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
                
                PyObject *anim_info_key, *anim_info_value;
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
        PyObject *anim_key, *anim_value;
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

#endif // HAVE_PYTHON