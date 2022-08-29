#include "cActor_ext.h"

#ifdef HAVE_PYTHON

#define PyString_Check(obj) (PyUnicode_Check(obj) != 0 || PyBytes_Check(obj) != 0)

std::string PyString_ToString(PyObject *obj) {
    char *str = NULL;
    Py_ssize_t str_len = 0;
    
    if (obj == NULL || obj == Py_None) { return std::string(""); }
                
    PyObject *bytesObj = obj;
    if (PyUnicode_Check(obj) != 0) {
        bytesObj = PyUnicode_AsASCIIString(obj);
    }
    
    int success = PyBytes_AsStringAndSize(bytesObj, &str, &str_len);
    if (success == -1) { return std::string(""); }
    return std::string(str, str_len);
}

void Extension<CActor>::__init__(PyObject *self, PyObject *models, PyObject *anims, PyObject *other, PyObject *copy,
                                 PyObject *lod_node, PyObject *flattenable, PyObject *set_final, PyObject *ok_missing) {

    // Any and all needed types.
    Dtool_TypeMap *tmap = Dtool_GetGlobalTypeMap();
    Dtool_TypeMap::const_iterator it = tmap->find("NodePath");
    Dtool_PyTypedObject *NodePath_py_type = (*it).second;

    bool _copy = true;
    bool _flattenable = true;
    bool _set_final = false;
    bool _ok_missing = true;

    // Use _this instead of this.
    
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
            if (anims != Py_None) { PyDict_Next(anims, &anim_pos, &anim_key, &anim_value); }
            
            // If the model_value isn't a dict object, Then it isn't a multi-part actor w/ LOD.
            // But if it is, We will loop the models dictionary and it's sub dictionaries.
            // If the anim_value isn't a dict object, Then it isn't a multipart actor w/o LOD.
            // In that case, It will be a single part actor w/ LOD.
            if (PyDict_Check(model_value)) {
                // Get and set our lod node from the python object.
                NodePath *lod_node_ptr = NULL;
                if (lod_node != Py_None && DtoolInstance_GetPointer(lod_node, lod_node_ptr, *NodePath_py_type)) {
                    _this->set_lod_node(*lod_node_ptr);
                }
                
                // Preserve numerical order for lod's
                // This will make it easier to set ranges
                PyObject *keys = PyDict_Keys(models);
                PyList_Sort(keys);
                
                // Iterate the list.
                Py_ssize_t key_size = PyList_Size(keys);
                for (Py_ssize_t i = 0; i < key_size; i++) {
                    PyObject *key = PyList_GetItem(keys, i);
                    
                    std::string lod_name = PyString_ToString(key);
                    
                    // Make a node under the LOD switch
                    // for each LOD (Just because!)
                    _this->add_lod(lod_name);
                    
                    PyObject *lod_models = PyDict_GetItem(models, key);
                    PyObject *lod_model_key, *lod_model_value;
                    Py_ssize_t lod_model_pos = 0;
                    
                    // Iterate over the internal dict
                    while (PyDict_Next(lod_models, &lod_model_pos, &lod_model_key, &lod_model_value)) {
                        _this->load_model(PyString_ToString(lod_model_value), PyString_ToString(lod_model_key), lod_name, _copy, _ok_missing);
                    }
                }
            } else if (anims != Py_None && PyDict_Check(anim_value)) {
                while (PyDict_Next(models, &model_pos, &model_key, &model_value)) {
                    _this->load_model(PyString_ToString(model_value), PyString_ToString(model_key), "lodRoot", _copy, _ok_missing);
                }
            } else {
                // Get and set our lod node from the python object.
                NodePath *lod_node_ptr = NULL;
                if (lod_node != Py_None && DtoolInstance_GetPointer(lod_node, lod_node_ptr, *NodePath_py_type)) {
                    _this->set_lod_node(*lod_node_ptr);
                }
                
                // Preserve numerical order for lod's
                // This will make it easier to set ranges
                PyObject *keys = PyDict_Keys(models);
                PyList_Sort(keys);
                
                // Iterate the list.
                Py_ssize_t key_size = PyList_Size(keys);
                for (Py_ssize_t i = 0; i < key_size; i++) {
                    PyObject *key = PyList_GetItem(keys, i);
                    
                    std::string lod_name = PyString_ToString(key);
                    
                    // Make a node under the LOD switch
                    // for each LOD (Just because!)
                    _this->add_lod(lod_name);
                    
                    PyObject *model_value = PyDict_GetItem(models, key);
                    
                    _this->load_model(PyString_ToString(model_value), "modelRoot", lod_name, _copy, _ok_missing);
                }
            }
        } else if (PyString_Check(models) != 0) {
            std::string models_str = PyString_ToString(models);

            _this->load_model(models_str, "modelRoot", "lodRoot", _copy, _ok_missing);
        } else {
            std::ostringstream stream;
            stream << "models paramater passed to CActor constructor must be a dict or a str.";
            std::string str = stream.str();
            PyErr_SetString(PyExc_TypeError, str.c_str());
            return;
        }
        
        if (PyDict_Check(anims) != 0) {

        }
    } else {
        // Actor Copy Here.
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

#endif // HAVE_PYTHON