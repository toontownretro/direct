#include "cActor.h"
#include "config_actor.h"

CActor::CActor() {
    
}

CActor::CActor(std::string &modelName, bool copy, bool flattenable, bool set_final, bool ok_missing) {
    bool got_name = false;
    
    if (flattenable) {
        // If we want a flattenable Actor, don't create all
        // those ModelNodes, and the GeomNode is the same as
        // the root.
        NodePath this_path(this->node());
        PT(PandaNode) root = new PandaNode("actor");
        //assign(NodePath(root));
        set_geom_node(this_path);
    } else {
        // A standard Actor has a ModelNode at the root, and
        // another ModelNode to protect the GeomNode.
        PT(ModelRoot) root = new ModelRoot("actor");
        root->set_preserve_transform(ModelNode::PreserveTransform::PT_local);
        //assign(NodePath(root));
        PT(ModelNode) mNode = new ModelNode("actorGeom");
        NodePath attached_node = attach_new_node(mNode);
        set_geom_node(attached_node);
    }
    
    if (set_final) {
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
        _geom_node.node()->set_final(true);
    }
}

CActor::CActor(const CActor &other) {
    
}

CActor::~CActor() {
    
}

void CActor::load_model(NodePath &model_path, std::string &part_name, std::string &lod_name, bool copy, bool ok_missing, bool auto_bind_anims, bool keep_model) {
    NodePath model, bundle_np, node_to_parent;
    
    actor_cat.debug() << "in loadModel: " << model_path << ", part: " << part_name << ", lod: " << lod_name << ", copy: " << copy << "\n";
    
    if (copy) {
        model = model_path.copy_to(NodePath());
    } else {
        model = model_path;
    }
    
    if (model.node()->is_of_type(CharacterNode::get_class_type())) {
        bundle_np = model;
    } else {
        bundle_np = model.find("**/+CharacterNode");
    }
    
    if (bundle_np.is_empty()) {
        actor_cat.warning() << model_path << " is not a character!\n";
        model.reparent_to(_geom_node);
        return;
    }

    // Any animations and sequences that were bundled in with the model
    // should already exist on the Character at this point.

    // Now extract out the Character and integrate it with
    // the Actor.
    
    node_to_parent = keep_model ? model : bundle_np;
    
    if (lod_name.compare("lodRoot") != 0) {
        // parent to appropriate node under LOD switch
        node_to_parent.reparent_to(_lod_node.find(lod_name));
    } else {
        node_to_parent.reparent_to(_geom_node);
    }
    
    //prepare_bundle(bundle_np, model, part_name, lod_name);
    
    // we rename this node to make Actor copying easier
    bundle_np.node()->set_name(part_prefix + part_name);
}


int CActor::PartDef::get_channel_index(std::string &anim_name) {
    pmap<std::string, AnimDef>::iterator g = _anims_by_name.find(anim_name);
    if (g == _anims_by_name.end()) {
        return -1;
    }
    return g->second.get_index();
}

CActor::AnimDef *CActor::PartDef::get_anim_def(int index) {
    if (index >= _anims_by_index.size()) {
        return nullptr;
    }
    return &_anims_by_index[index];
}

CActor::AnimDef *CActor::PartDef::get_anim_def(std::string &anim_name) {
    pmap<std::string, AnimDef>::iterator g = _anims_by_name.find(anim_name);
    if (g == _anims_by_name.end()) {
        return nullptr;
    }
    return &g->second;
}