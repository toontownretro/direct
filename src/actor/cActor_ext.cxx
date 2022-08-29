#include "cActor_ext.h"

#ifdef HAVE_PYTHON

#ifndef CPPPARSER
extern struct Dtool_PyTypedObject Dtool_NodePath;
#ifdef STDFLOAT_DOUBLE
extern struct Dtool_PyTypedObject Dtool_LPoint3d;
#else
extern struct Dtool_PyTypedObject Dtool_LPoint3f;
#endif
#endif

#define PyString_Check(obj) (PyUnicode_Check(obj) != 0 || PyBytes_Check(obj) != 0)

std::string PyString_ToString(PyObject *obj) {
    char *str = NULL;
    Py_ssize_t str_len = 0;
                
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
        if (models != Py_None) {
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
                    //NodePath *lod_node_ptr = NULL;
                    //if (lod_node != Py_None && DtoolInstance_GetPointer(lod_node, lod_node_ptr, Dtool_NodePath)) {
                    //    _this->set_lod_node(*lod_node_ptr);
                    //}
                    
                    // Normally we'd sort the dictonary by getting the keys and turning them into a list and then sort and iterate those.
                    // But there's no way to do it in C++ without it being a hassle. So whatever.
                    
                    
                    while (PyDict_Next(models, &model_pos, &model_key, &model_value)) {
                        
                    }
                } else if (anims != Py_None && PyDict_Check(anim_value)) {
                    while (PyDict_Next(anims, &anim_pos, &anim_key, &anim_value)) {
                        
                    }
                } else {
                    
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
        }
        
        if (anims != Py_None) {

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