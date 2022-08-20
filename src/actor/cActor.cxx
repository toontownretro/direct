#include "cActor.h"
#include "config_actor.h"

#include "jobSystem.h"
#include "transformState.h"

#define EMPTY_STR std::string("")

//////////////////////////////
// Initializers w/o Animations
//////////////////////////////

CActor::CActor(bool flattenable, bool set_final) : NodePath() {
    initialize_geom_node(flattenable);
    
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

CActor::CActor(const std::string &model_path, bool copy, bool flattenable, bool set_final, bool ok_missing) : NodePath() {
    initialize_geom_node(flattenable);
    
    // Single-part Actor w/o LOD
    load_model(model_path, EMPTY_STR, EMPTY_STR, copy, ok_missing);
    
    if (set_final) {
        // If set_final is true, the Actor will set its top bounding
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

CActor::CActor(const NodePath &model_node, bool copy, bool flattenable, bool set_final, bool ok_missing) : NodePath() {
    initialize_geom_node(flattenable);
    
    // Single-part Actor w/o LOD
    load_model(model_node, EMPTY_STR, EMPTY_STR, copy, ok_missing);
    
    if (set_final) {
        // If set_final is true, the Actor will set its top bounding
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

CActor::CActor(const pmap<std::string, std::string> &models, bool copy, bool flattenable, bool set_final, bool ok_missing) : NodePath() {
    initialize_geom_node(flattenable);
    
    // Multi-part Actor w/o LOD
    for (pmap<std::string, std::string>::const_iterator it = models.begin(); it != models.end(); it++) {
        std::string part_name = it->first;
        std::string model_path = it->second;
        load_model(model_path, part_name, EMPTY_STR, copy, ok_missing);
        
    }
        
    if (set_final) {
        // If set_final is true, the Actor will set its top bounding
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

CActor::CActor(const pmap<std::string, NodePath> &models, bool copy, bool flattenable, bool set_final, bool ok_missing) : NodePath() {
    initialize_geom_node(flattenable);

    // Multi-part Actor w/o LOD
    for (pmap<std::string, NodePath>::const_iterator it = models.begin(); it != models.end(); it++) {
        std::string part_name = it->first;
        const NodePath &model_node = it->second;
        load_model(model_node, part_name, EMPTY_STR, copy, ok_missing);
        
    }
    
    if (set_final) {
        // If set_final is true, the Actor will set its top bounding
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

CActor::CActor(const pmap<std::string, std::string> &models, NodePath &lod_node, bool copy, bool flattenable, bool set_final, bool ok_missing) : NodePath() {
    pvector<std::string> lod_names;
    
    initialize_geom_node(flattenable);
    
    if (lod_node.is_empty()) {
        actor_cat.error() << "Failed to initialize Actor with lod because the LOD Node is empty!\n";
        return; 
    }

    // Single-part Actor w/ LOD
    set_lod_node(lod_node);
    for (pmap<std::string, std::string>::const_iterator it = models.begin(); it != models.end(); it++) {
        std::string lod_name = it->first;
        std::string model_path = it->second;
        
        // Add the lod name to the list we have, All duplicates will be removed.
        lod_names.push_back(lod_name);
        load_model(model_path, EMPTY_STR, lod_name, copy, ok_missing);
    }
    
    // Remove any duplicates.
    std::sort(lod_names.begin(), lod_names.end());
    lod_names.erase(std::unique(lod_names.begin(), lod_names.end()), lod_names.end());
    
    for (size_t i = 0; i < lod_names.size(); i++) {
        // Add our new lod to our lods.
        add_lod(lod_names[i]);
    }
    
    if (set_final) {
        // If set_final is true, the Actor will set its top bounding
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

CActor::CActor(const pmap<std::string, NodePath> &models, NodePath &lod_node, bool copy, bool flattenable, bool set_final, bool ok_missing) : NodePath() {
    pvector<std::string> lod_names;
    
    initialize_geom_node(flattenable);
    
    if (lod_node.is_empty()) {
        actor_cat.error() << "Failed to initialize Actor with lod because the LOD Node is empty!\n";
        return; 
    }

    // Single-part Actor w/ LOD
    set_lod_node(lod_node);
    for (pmap<std::string, NodePath>::const_iterator it = models.begin(); it != models.end(); it++) {
        std::string lod_name = it->first;
        const NodePath &model_node = it->second;
        
        // Add the lod name to the list we have, All duplicates will be removed.
        lod_names.push_back(lod_name);
        load_model(model_node, EMPTY_STR, lod_name, copy, ok_missing);
    }
    
    // Remove any duplicates.
    std::sort(lod_names.begin(), lod_names.end());
    lod_names.erase(std::unique(lod_names.begin(), lod_names.end()), lod_names.end());
    
    for (size_t i = 0; i < lod_names.size(); i++) {
        // Add our new lod to our lods.
        add_lod(lod_names[i]);
    }
    
    if (set_final) {
        // If set_final is true, the Actor will set its top bounding
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

CActor::CActor(const pvector<MultipartLODActorDataWPath> &models, NodePath &lod_node, bool copy, bool flattenable, bool set_final, bool ok_missing) : NodePath() {
    pvector<std::string> lod_names;
    
    initialize_geom_node(flattenable);
    
    if (lod_node.is_empty()) {
        actor_cat.error() << "Failed to initialize Actor with lod because the LOD Node is empty!\n";
        return; 
    }
    
    // Multi-part Actor w/ LOD
    set_lod_node(lod_node);
    for (size_t i = 0; i < models.size(); i++) {
        MultipartLODActorDataWPath data = models[i];
        
        // Add the lod name to the list we have, All duplicates will be removed.
        lod_names.push_back(data.lod_name);
        load_model(data.model_path, data.part_name, data.lod_name, copy, ok_missing);
    }
    
    // Remove any duplicates.
    std::sort(lod_names.begin(), lod_names.end());
    lod_names.erase(std::unique(lod_names.begin(), lod_names.end()), lod_names.end());
    
    for (size_t i = 0; i < lod_names.size(); i++) {
        // Add our new lod to our lods.
        add_lod(lod_names[i]);
    }
    
    if (set_final) {
        // If set_final is true, the Actor will set its top bounding
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

CActor::CActor(const pvector<MultipartLODActorData> &models, NodePath &lod_node, bool copy, bool flattenable, bool set_final, bool ok_missing) : NodePath() {
    pvector<std::string> lod_names;
    
    initialize_geom_node(flattenable);
    
    if (lod_node.is_empty()) {
        actor_cat.error() << "Failed to initialize Actor with lod because the LOD Node is empty!\n";
        return; 
    }
    
    // Multi-part Actor w/ LOD
    set_lod_node(lod_node);
    for (size_t i = 0; i < models.size(); i++) {
        MultipartLODActorData data = models[i];
        
        // Add the lod name to the list we have, All duplicates will be removed.
        lod_names.push_back(data.lod_name);
        load_model(data.model_node, data.part_name, data.lod_name, copy, ok_missing);
    }
    
    // Remove any duplicates.
    std::sort(lod_names.begin(), lod_names.end());
    lod_names.erase(std::unique(lod_names.begin(), lod_names.end()), lod_names.end());
    
    for (size_t i = 0; i < lod_names.size(); i++) {
        // Add our new lod to our lods.
        add_lod(lod_names[i]);
    }
    
    if (set_final) {
        // If set_final is true, the Actor will set its top bounding
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

//////////////////////////////
// Initializers w/ Animations
//////////////////////////////

CActor::CActor(const std::string &model_path, const pvector<std::pair<std::string, std::string> > &anims, bool copy, bool flattenable, bool set_final, bool ok_missing) : NodePath() {
    initialize_geom_node(flattenable);
    
    // Single-part Actor w/o LOD
    load_model(model_path, EMPTY_STR, EMPTY_STR, copy, ok_missing);
    load_anims(anims, EMPTY_STR, EMPTY_STR);
    
    if (set_final) {
        // If set_final is true, the Actor will set its top bounding
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

CActor::CActor(const NodePath &model_node, const pvector<std::pair<std::string, std::string> > &anims, bool copy, bool flattenable, bool set_final, bool ok_missing) : NodePath() {
    initialize_geom_node(flattenable);
    
    // Single-part Actor w/o LOD
    load_model(model_node, EMPTY_STR, EMPTY_STR, copy, ok_missing);
    load_anims(anims, EMPTY_STR, EMPTY_STR);
    
    if (set_final) {
        // If set_final is true, the Actor will set its top bounding
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

CActor::CActor(const pmap<std::string, std::string> &models, const pmap<std::string, pvector<std::pair<std::string, std::string> > > &anims, bool copy, bool flattenable, bool set_final, bool ok_missing) : NodePath() {
    initialize_geom_node(flattenable);
    
    // Multi-part Actor w/o LOD
    for (pmap<std::string, std::string>::const_iterator it = models.begin(); it != models.end(); it++) {
        std::string part_name = it->first;
        std::string model_path = it->second;
        load_model(model_path, part_name, EMPTY_STR, copy, ok_missing);
        
    }
    
    for (pmap<std::string, pvector<std::pair<std::string, std::string> > >::const_iterator it = anims.begin(); it != anims.end(); it++) {
        std::string part_name = it->first;
        pvector<std::pair<std::string, std::string> > part_anims = it->second;
        
        load_anims(part_anims, part_name, EMPTY_STR);
    }
        
    if (set_final) {
        // If set_final is true, the Actor will set its top bounding
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

CActor::CActor(const pmap<std::string, NodePath> &models, const pmap<std::string, pvector<std::pair<std::string, std::string> > > &anims, bool copy, bool flattenable, bool set_final, bool ok_missing) : NodePath() {
    initialize_geom_node(flattenable);

    // Multi-part Actor w/o LOD
    for (pmap<std::string, NodePath>::const_iterator it = models.begin(); it != models.end(); it++) {
        std::string part_name = it->first;
        const NodePath &model_node = it->second;
        load_model(model_node, part_name, EMPTY_STR, copy, ok_missing);
        
    }
    
    for (pmap<std::string, pvector<std::pair<std::string, std::string> > >::const_iterator it = anims.begin(); it != anims.end(); it++) {
        std::string part_name = it->first;
        pvector<std::pair<std::string, std::string> > part_anims = it->second;
        
        load_anims(part_anims, part_name, EMPTY_STR);
    }
    
    if (set_final) {
        // If set_final is true, the Actor will set its top bounding
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

CActor::CActor(const pmap<std::string, std::string> &models, NodePath &lod_node, const pvector<std::pair<std::string, std::string> > &anims, bool copy, bool flattenable, bool set_final, bool ok_missing) : NodePath() {
    pvector<std::string> lod_names;
    
    initialize_geom_node(flattenable);
    
    if (lod_node.is_empty()) {
        actor_cat.error() << "Failed to initialize Actor with lod because the LOD Node is empty!\n";
        return; 
    }

    // Single-part Actor w/ LOD
    set_lod_node(lod_node);
    for (pmap<std::string, std::string>::const_iterator it = models.begin(); it != models.end(); it++) {
        std::string lod_name = it->first;
        std::string model_path = it->second;
        
        // Add the lod name to the list we have, All duplicates will be removed.
        lod_names.push_back(lod_name);
        load_model(model_path, EMPTY_STR, lod_name, copy, ok_missing);
    }
    
    // Remove any duplicates.
    std::sort(lod_names.begin(), lod_names.end());
    lod_names.erase(std::unique(lod_names.begin(), lod_names.end()), lod_names.end());
    
    for (size_t i = 0; i < lod_names.size(); i++) {
        // Add our new lod to our lods.
        add_lod(lod_names[i]);
        load_anims(anims, EMPTY_STR, lod_names[i]);
    }
    
    if (set_final) {
        // If set_final is true, the Actor will set its top bounding
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

CActor::CActor(const pmap<std::string, NodePath> &models, NodePath &lod_node, const pvector<std::pair<std::string, std::string> > &anims, bool copy, bool flattenable, bool set_final, bool ok_missing) : NodePath() {
    pvector<std::string> lod_names;
    
    initialize_geom_node(flattenable);
    
    if (lod_node.is_empty()) {
        actor_cat.error() << "Failed to initialize Actor with lod because the LOD Node is empty!\n";
        return; 
    }

    // Single-part Actor w/ LOD
    set_lod_node(lod_node);
    for (pmap<std::string, NodePath>::const_iterator it = models.begin(); it != models.end(); it++) {
        std::string lod_name = it->first;
        const NodePath &model_node = it->second;
        
        // Add the lod name to the list we have, All duplicates will be removed.
        lod_names.push_back(lod_name);
        load_model(model_node, EMPTY_STR, lod_name, copy, ok_missing);
    }
    
    // Remove any duplicates.
    std::sort(lod_names.begin(), lod_names.end());
    lod_names.erase(std::unique(lod_names.begin(), lod_names.end()), lod_names.end());
    
    for (size_t i = 0; i < lod_names.size(); i++) {
        // Add our new lod to our lods.
        add_lod(lod_names[i]);
        load_anims(anims, EMPTY_STR, lod_names[i]);
    }
    
    if (set_final) {
        // If set_final is true, the Actor will set its top bounding
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

CActor::CActor(const pvector<MultipartLODActorDataWPath> &models, NodePath &lod_node, const pmap<std::string, pvector<std::pair<std::string, std::string> > > &anims, 
               bool copy, bool flattenable, bool set_final, bool ok_missing) : NodePath() {
    pvector<std::string> lod_names;
    
    initialize_geom_node(flattenable);
    
    if (lod_node.is_empty()) {
        actor_cat.error() << "Failed to initialize Actor with lod because the LOD Node is empty!\n";
        return; 
    }
    
    // Multi-part Actor w/ LOD
    set_lod_node(lod_node);
    for (size_t i = 0; i < models.size(); i++) {
        MultipartLODActorDataWPath data = models[i];
        
        // Add the lod name to the list we have, All duplicates will be removed.
        lod_names.push_back(data.lod_name);
        load_model(data.model_path, data.part_name, data.lod_name, copy, ok_missing);
    }
    
    // Remove any duplicates.
    std::sort(lod_names.begin(), lod_names.end());
    lod_names.erase(std::unique(lod_names.begin(), lod_names.end()), lod_names.end());
    
    for (size_t i = 0; i < lod_names.size(); i++) {
        // Add our new lod to our lods.
        add_lod(lod_names[i]);
        
        for (pmap<std::string, pvector<std::pair<std::string, std::string> > >::const_iterator it = anims.begin(); it != anims.end(); it++) {
            std::string part_name = it->first;
            pvector<std::pair<std::string, std::string> > part_anims = it->second;
            
            load_anims(part_anims, part_name, lod_names[i]);
        }
    }
    
    if (set_final) {
        // If set_final is true, the Actor will set its top bounding
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

CActor::CActor(const pvector<MultipartLODActorData> &models, NodePath &lod_node, const pmap<std::string, pvector<std::pair<std::string, std::string> > > &anims, 
               bool copy, bool flattenable, bool set_final, bool ok_missing) : NodePath() {
    pvector<std::string> lod_names;
    
    initialize_geom_node(flattenable);
    
    if (lod_node.is_empty()) {
        actor_cat.error() << "Failed to initialize Actor with lod because the LOD Node is empty!\n";
        return; 
    }
    
    // Multi-part Actor w/ LOD
    set_lod_node(lod_node);
    for (size_t i = 0; i < models.size(); i++) {
        MultipartLODActorData data = models[i];
        
        // Add the lod name to the list we have, All duplicates will be removed.
        lod_names.push_back(data.lod_name);
        load_model(data.model_node, data.part_name, data.lod_name, copy, ok_missing);
    }
    
    // Remove any duplicates.
    std::sort(lod_names.begin(), lod_names.end());
    lod_names.erase(std::unique(lod_names.begin(), lod_names.end()), lod_names.end());
    
    for (size_t i = 0; i < lod_names.size(); i++) {
        // Add our new lod to our lods.
        add_lod(lod_names[i]);
        
        for (pmap<std::string, pvector<std::pair<std::string, std::string> > >::const_iterator it = anims.begin(); it != anims.end(); it++) {
            std::string part_name = it->first;
            pvector<std::pair<std::string, std::string> > part_anims = it->second;
            
            load_anims(part_anims, part_name, lod_names[i]);
        }
    }
    
    if (set_final) {
        // If set_final is true, the Actor will set its top bounding
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
    _got_name = other._got_name;
    
    // Assign these elements to ourself (overwrite)
    NodePath other_copy = other.copy_to(NodePath());
    other_copy.detach_node();
    
    // The C++ equivalent of assign() for a NodePath in Python.
    NodePath::operator=(other_copy);
    
    // masad: Check if other_copy has a GeomNode as its first child,
    // If CActor is initialized with flattenable, then other_copy, not
    // its first child, is the geom node; Check initialize_geom_node, for reference.
    if (other.get_geom_node().get_name().compare(other.get_name()) == 0) {
        set_geom_node(other_copy);
    } else {
        set_geom_node(other_copy.get_child(0));
    }
    
    _switches.insert(other._switches.begin(), other._switches.end());
    
    _lod_node = find("**/+LODNode");
    if (!_lod_node.is_empty()) { _has_LOD = true; }
    
    copy_part_bundles(other);
}

CActor::~CActor() {
    
}

void CActor::operator=(const CActor &copy) {
    _got_name = copy._got_name;
    
    // Just copy these to ourselves.
    NodePath node_copy = copy.copy_to(*this);
    
    // masad: Check if node_copy has a GeomNode as its first child,
    // If CActor is initialized with flattenable, then node_copy, not
    // its first child, is the geom node; Check initialize_geom_node, for reference.
    if (copy.get_geom_node().get_name().compare(copy.get_name()) == 0) {
        set_geom_node(node_copy);
    } else {
        set_geom_node(node_copy.get_child(0));
    }
    
    _switches.insert(copy._switches.begin(), copy._switches.end());
    
    _lod_node = find("**/+LODNode");
    if (!_lod_node.is_empty()) { _has_LOD = true; }
    
    copy_part_bundles(copy);
}

void CActor::initialize_geom_node(bool flattenable) {
    if (flattenable) {
        // If we want a flattenable Actor, don't create all
        // those ModelNodes, and the GeomNode is the same as
        // the root.
        NodePath this_path(this->node());
        PT(PandaNode) root = new PandaNode("actor");
        
        // The C++ equivalent of assign() for a NodePath in Python.
        NodePath::operator=(NodePath(root));
        
        set_geom_node(this_path);
    } else {
        // A standard Actor has a ModelNode at the root, and
        // another ModelNode to protect the GeomNode.
        PT(ModelRoot) root = new ModelRoot("actor");
        root->set_preserve_transform(ModelNode::PreserveTransform::PT_local);
        
        // The C++ equivalent of assign() for a NodePath in Python.
        NodePath::operator=(NodePath(root));
        
        PT(ModelNode) mNode = new ModelNode("actorGeom");
        NodePath attached_node = attach_new_node(mNode);
        set_geom_node(attached_node);
    }
}
        
/**
 * copy_part_bundles(CActor)
 *
 * Copy the part bundle dictionary from another actor as this
 * instances own. NOTE: This method does not actually copy geometry!
**/
void CActor::copy_part_bundles(const CActor &other) {
    for (pmap<std::string, PartDef>::const_iterator it = other._part_bundle_dict.begin(); it != other._part_bundle_dict.end(); it++) {
        NodePath part_lod;
        
        std::string bundle_name(it->first);
        PartDef part_def = it->second;
        
        // Get back both our lod name and our part name by splitting the string.
        std::string lod_name = bundle_name.substr(0, bundle_name.find(':'));
        // Erase the lod name and the delimiter.
        bundle_name.erase(0, bundle_name.find(':') + 1);
        // The bundle name is now the part name.
        std::string part_name = bundle_name;
        
        if (lod_name.compare("lodRoot") == 0) {
            part_lod = *this;
        } else {
            part_lod = _lod_node.find(lod_name);
        }
        
        if (part_lod.is_empty()) {
            actor_cat.warning() << "No LOD named: " << lod_name << '\n';
            return;
        }
        
        // Find the part in our tree.
        NodePath bundle_np = part_lod.find("**/" + part_prefix + part_name);
        if (bundle_np.is_empty()) {
            actor_cat.error() << "LOD: " << lod_name << " has no matching part: " << part_name << '\n';
            continue;
        }
        
        prepare_bundle(bundle_np, part_def._part_model, part_name, lod_name);
        
        PartDef our_part_def = _part_bundle_dict[it->first];
        our_part_def._weight_list.insert(part_def._weight_list.begin(), part_def._weight_list.end());
        our_part_def._anims_by_name.insert(part_def._anims_by_name.begin(), part_def._anims_by_name.end());
    }
}
        
/**
 * stop(layer=-1, kill=false)
 *
 * Stop named animation on the given part of the actor.
 * If no name specified then stop all animations on the actor.
 * NOTE: Stops all LODs.
**/
void CActor::stop(int layer, bool kill) {
    pvector<PartDef> part_defs = get_part_defs();
    
    // Stopping all layers or a specific layer
    for (size_t i = 0; i < part_defs.size(); i++) {
        PartDef part_def = part_defs[i];
        PT(Character) character = part_def._character;
        if (character == nullptr) { continue; }
        if (layer == -1 || layer < character->get_num_anim_layers()) { character->stop(layer, kill); }
    }
}

/**
 * stop(string, string, layer=-1, kill=false)
 *
 * Stop named animation on the given part of the actor.
 * If no name specified then stop all animations on the actor.
 * NOTE: Stops all LODs.
**/
void CActor::stop(const std::string &anim_name, const std::string &part_name, int layer, bool kill) {
    bool has_anim_name = !anim_name.empty();
    
    // If both strings are empty for some reason, Just call the version that needs no
    // paramaters.
    if (!has_anim_name && part_name.empty()) { stop(layer, kill); return; }
    
    pvector<PartDef> part_defs = get_part_defs(part_name, EMPTY_STR);
    
    for (size_t i = 0; i < part_defs.size(); i++) {
        PartDef part_def = part_defs[i];
        PT(Character) character = part_def._character;
        if (character == nullptr) { continue; }
        
        // Stopping all layers or a specific layer for a part.
        if (!has_anim_name) {
            if (layer == -1 || layer < character->get_num_anim_layers()) { character->stop(layer, kill); }
            continue;
        }
            
        int channel_index = part_def.get_channel_index(anim_name);
        if (channel_index <= -1) { continue; }
        for (int i = 0; i < character->get_num_anim_layers(); i++) {
            AnimLayer *anim_layer = character->get_anim_layer(i);
            if (anim_layer == nullptr) { continue; }
            if (anim_layer->_sequence == channel_index) {
                // This layer is playing the channel we want to stop.
                character->stop(layer, kill);
            }
        }
    }
}
        
/**
 * play(string, int=0, int=-1, int=0, float=1.0, bool=false, float=0.0, float=0.0)
 *
 * Play the given animation on the given part of the actor.
 * If no part is specified, try to play on all parts. 
 * NOTE: Plays over ALL LODs.
**/
void CActor::play(const std::string &anim_name, int from_frame, int to_frame, int layer, PN_stdfloat play_rate, bool auto_kill, PN_stdfloat blend_in, PN_stdfloat blend_out) {
    pvector<AnimDef> anim_defs = get_anim_defs(anim_name);
    
    for (size_t i = 0; i < anim_defs.size(); i++) {
        AnimDef anim_def = anim_defs[i];
        PT(Character) character = anim_def.get_character();
        if (character == nullptr) { continue; }
        
        // If no last frame is specified, We want the full animation.
        if (to_frame <= -1) {
            PT(AnimChannel) channel = anim_def.get_animation_channel();
            if (channel != nullptr) { 
                to_frame = channel->get_num_frames() - 1;
            } else {
                to_frame = 0;
            }
        }
        
        character->play(anim_def.get_index(), from_frame, to_frame, layer, anim_def.get_play_rate() * play_rate, auto_kill, blend_in, blend_out);
    }
}

/**
 * play(int, int=0, int=-1, int=0, float=1.0, bool=false, float=0.0, float=0.0)
 *
 * Play the given animation on the given part of the actor.
 * If no part is specified, try to play on all parts. 
 * NOTE: Plays over ALL LODs.
**/
void CActor::play(int channel, int from_frame, int to_frame, int layer, PN_stdfloat play_rate, bool auto_kill, PN_stdfloat blend_in, PN_stdfloat blend_out) {
    pvector<AnimDef> anim_defs = get_anim_defs(channel);
    
    for (size_t i = 0; i < anim_defs.size(); i++) {
        AnimDef anim_def = anim_defs[i];
        PT(Character) character = anim_def.get_character();
        if (character == nullptr) { continue; }
        
        // If no last frame is specified, We want the full animation.
        if (to_frame <= -1) {
            PT(AnimChannel) channel = anim_def.get_animation_channel();
            if (channel != nullptr) { 
                to_frame = channel->get_num_frames() - 1;
            } else {
                to_frame = 0;
            }
        }
        
        character->play(anim_def.get_index(), from_frame, to_frame, layer, anim_def.get_play_rate() * play_rate, auto_kill, blend_in, blend_out);
    }
}

/**
 * play(string, string, int=0, int=-1, int=0, float=1.0, bool=false, float=0.0, float=0.0)
 *
 * Play the given animation on the given part of the actor.
 * If no part is specified, try to play on all parts. 
 * NOTE: Plays over ALL LODs.
**/
void CActor::play(const std::string &anim_name, const std::string &part_name, int from_frame, int to_frame, int layer, PN_stdfloat play_rate, bool auto_kill, PN_stdfloat blend_in, PN_stdfloat blend_out) {
    pvector<AnimDef> anim_defs = get_anim_defs(anim_name, part_name, EMPTY_STR);
    
    for (size_t i = 0; i < anim_defs.size(); i++) {
        AnimDef anim_def = anim_defs[i];
        PT(Character) character = anim_def.get_character();
        if (character == nullptr) { continue; }
        
        // If no last frame is specified, We want the full animation.
        if (to_frame <= -1) {
            PT(AnimChannel) channel = anim_def.get_animation_channel();
            if (channel != nullptr) { 
                to_frame = channel->get_num_frames() - 1;
            } else {
                to_frame = 0;
            }
        }
        
        character->play(anim_def.get_index(), from_frame, to_frame, layer, anim_def.get_play_rate() * play_rate, auto_kill, blend_in, blend_out);
    }
}

/**
 * play(int, string, int=0, int=-1, int=0, float=1.0, bool=false, float=0.0, float=0.0)
 *
 * Play the given animation on the given part of the actor.
 * If no part is specified, try to play on all parts. 
 * NOTE: Plays over ALL LODs.
**/
void CActor::play(int channel, const std::string &part_name, int from_frame, int to_frame, int layer, PN_stdfloat play_rate, bool auto_kill, PN_stdfloat blend_in, PN_stdfloat blend_out) {
    pvector<AnimDef> anim_defs = get_anim_defs(channel, part_name, EMPTY_STR);
    
    for (size_t i = 0; i < anim_defs.size(); i++) {
        AnimDef anim_def = anim_defs[i];
        PT(Character) character = anim_def.get_character();
        if (character == nullptr) { continue; }
        
        // If no last frame is specified, We want the full animation.
        if (to_frame <= -1) {
            PT(AnimChannel) channel = anim_def.get_animation_channel();
            if (channel != nullptr) { 
                to_frame = channel->get_num_frames() - 1;
            } else {
                to_frame = 0;
            }
        }
        
        character->play(anim_def.get_index(), from_frame, to_frame, layer, anim_def.get_play_rate() * play_rate, auto_kill, blend_in, blend_out);
    }
}

/**
 * loop(string, bool=true, int=0, int=-1, int=0, float=1.0, float=0.0)
 *
 * Loop the given animation on the given part of the actor,
 * restarting at zero frame if requested. If no part name
 * is given then try to loop on all parts. 
 * NOTE: Loops on all LODs.
**/
void CActor::loop(const std::string &anim_name, bool restart, int from_frame, int to_frame, int layer, PN_stdfloat play_rate, PN_stdfloat blend_in) {
    pvector<AnimDef> anim_defs = get_anim_defs(anim_name);
    
    for (size_t i = 0; i < anim_defs.size(); i++) {
        AnimDef anim_def = anim_defs[i];
        PT(Character) character = anim_def.get_character();
        if (character == nullptr) { continue; }
        
        // If no last frame is specified, We want the full animation.
        if (to_frame <= -1) {
            PT(AnimChannel) channel = anim_def.get_animation_channel();
            if (channel != nullptr) { 
                to_frame = channel->get_num_frames() - 1;
            } else {
                to_frame = 0;
            }
        }
        
        character->loop(anim_def.get_index(), restart, from_frame, to_frame, layer, anim_def.get_play_rate() * play_rate, blend_in);
    }
}

/**
 * loop(int, bool=true, int=0, int=-1, int=0, float=1.0, float=0.0)
 *
 * Loop the given animation on the given part of the actor,
 * restarting at zero frame if requested. If no part name
 * is given then try to loop on all parts. 
 * NOTE: Loops on all LODs.
**/
void CActor::loop(int channel, bool restart, int from_frame, int to_frame, int layer, PN_stdfloat play_rate, PN_stdfloat blend_in) {
    pvector<AnimDef> anim_defs = get_anim_defs(channel);
    
    for (size_t i = 0; i < anim_defs.size(); i++) {
        AnimDef anim_def = anim_defs[i];
        PT(Character) character = anim_def.get_character();
        if (character == nullptr) { continue; }
        
        // If no last frame is specified, We want the full animation.
        if (to_frame <= -1) {
            PT(AnimChannel) channel = anim_def.get_animation_channel();
            if (channel != nullptr) { 
                to_frame = channel->get_num_frames() - 1;
            } else {
                to_frame = 0;
            }
        }
        
        character->loop(anim_def.get_index(), restart, from_frame, to_frame, layer, anim_def.get_play_rate() * play_rate, blend_in);
    }
}

/**
 * loop(string, string, bool=true, int=0, int=-1, int=0, float=1.0, float=0.0)
 *
 * Loop the given animation on the given part of the actor,
 * restarting at zero frame if requested. If no part name
 * is given then try to loop on all parts. 
 * NOTE: Loops on all LODs.
**/
void CActor::loop(const std::string &anim_name, const std::string &part_name, bool restart, int from_frame, int to_frame, int layer, PN_stdfloat play_rate, PN_stdfloat blend_in) {
    pvector<AnimDef> anim_defs = get_anim_defs(anim_name, part_name, EMPTY_STR);
    
    for (size_t i = 0; i < anim_defs.size(); i++) {
        AnimDef anim_def = anim_defs[i];
        PT(Character) character = anim_def.get_character();
        if (character == nullptr) { continue; }
        
        // If no last frame is specified, We want the full animation.
        if (to_frame <= -1) {
            PT(AnimChannel) channel = anim_def.get_animation_channel();
            if (channel != nullptr) { 
                to_frame = channel->get_num_frames() - 1;
            } else {
                to_frame = 0;
            }
        }
        
        character->loop(anim_def.get_index(), restart, from_frame, to_frame, layer, anim_def.get_play_rate() * play_rate, blend_in);
    }
}

/**
 * loop(int, string, bool=true, int=0, int=-1, int=0, float=1.0, float=0.0)
 *
 * Loop the given animation on the given part of the actor,
 * restarting at zero frame if requested. If no part name
 * is given then try to loop on all parts. 
 * NOTE: Loops on all LODs.
**/
void CActor::loop(int channel, const std::string &part_name, bool restart, int from_frame, int to_frame, int layer, PN_stdfloat play_rate, PN_stdfloat blend_in) {
    pvector<AnimDef> anim_defs = get_anim_defs(channel, part_name, EMPTY_STR);
    
    for (size_t i = 0; i < anim_defs.size(); i++) {
        AnimDef anim_def = anim_defs[i];
        PT(Character) character = anim_def.get_character();
        if (character == nullptr) { continue; }
        
        // If no last frame is specified, We want the full animation.
        if (to_frame <= -1) {
            PT(AnimChannel) channel = anim_def.get_animation_channel();
            if (channel != nullptr) { 
                to_frame = channel->get_num_frames() - 1;
            } else {
                to_frame = 0;
            }
        }
        
        character->loop(anim_def.get_index(), restart, from_frame, to_frame, layer, anim_def.get_play_rate() * play_rate, blend_in);
    }
}

/**
 * pingpong(string, bool=true, int=0, int=-1, int=0, float=1.0, float=0.0)
 *
 * Plays the indicated animation channel on the indicated layer back and forth
 * repeatedly.
**/
void CActor::pingpong(const std::string &anim_name, bool restart, int from_frame, int to_frame, int layer, PN_stdfloat play_rate, PN_stdfloat blend_in) {
    pvector<AnimDef> anim_defs = get_anim_defs(anim_name);
    
    for (size_t i = 0; i < anim_defs.size(); i++) {
        AnimDef anim_def = anim_defs[i];
        PT(Character) character = anim_def.get_character();
        if (character == nullptr) { continue; }
        
        // If no last frame is specified, We want the full animation.
        if (to_frame <= -1) {
            PT(AnimChannel) channel = anim_def.get_animation_channel();
            if (channel != nullptr) { 
                to_frame = channel->get_num_frames() - 1;
            } else {
                to_frame = 0;
            }
        }
        
        character->pingpong(anim_def.get_index(), restart, from_frame, to_frame, layer, anim_def.get_play_rate() * play_rate, blend_in);
    }
}

/**
 * pingpong(int, bool=true, int=0, int=-1, int=0, float=1.0, float=0.0)
 *
 * Plays the indicated animation channel on the indicated layer back and forth
 * repeatedly.
**/
void CActor::pingpong(int channel, bool restart, int from_frame, int to_frame, int layer, PN_stdfloat play_rate, PN_stdfloat blend_in) {
    pvector<AnimDef> anim_defs = get_anim_defs(channel);
    
    for (size_t i = 0; i < anim_defs.size(); i++) {
        AnimDef anim_def = anim_defs[i];
        PT(Character) character = anim_def.get_character();
        if (character == nullptr) { continue; }
        
        // If no last frame is specified, We want the full animation.
        if (to_frame <= -1) {
            PT(AnimChannel) channel = anim_def.get_animation_channel();
            if (channel != nullptr) { 
                to_frame = channel->get_num_frames() - 1;
            } else {
                to_frame = 0;
            }
        }
        
        character->pingpong(anim_def.get_index(), restart, from_frame, to_frame, layer, anim_def.get_play_rate() * play_rate, blend_in);
    }
}

/**
 * pingpong(string, string, bool=true, int=0, int=-1, int=0, float=1.0, float=0.0)
 *
 * Plays the indicated animation channel on the indicated layer back and forth
 * repeatedly.
**/
void CActor::pingpong(const std::string &anim_name, const std::string &part_name, bool restart, int from_frame, int to_frame, int layer, PN_stdfloat play_rate, PN_stdfloat blend_in) {
    pvector<AnimDef> anim_defs = get_anim_defs(anim_name, part_name, EMPTY_STR);
    
    for (size_t i = 0; i < anim_defs.size(); i++) {
        AnimDef anim_def = anim_defs[i];
        PT(Character) character = anim_def.get_character();
        if (character == nullptr) { continue; }
        
        // If no last frame is specified, We want the full animation.
        if (to_frame <= -1) {
            PT(AnimChannel) channel = anim_def.get_animation_channel();
            if (channel != nullptr) { 
                to_frame = channel->get_num_frames() - 1;
            } else {
                to_frame = 0;
            }
        }
        
        character->pingpong(anim_def.get_index(), restart, from_frame, to_frame, layer, anim_def.get_play_rate() * play_rate, blend_in);
    }
}

/**
 * pingpong(int, string, bool=true, int=0, int=-1, int=0, float=1.0, float=0.0)
 *
 * Plays the indicated animation channel on the indicated layer back and forth
 * repeatedly.
**/
void CActor::pingpong(int channel, const std::string &part_name, bool restart, int from_frame, int to_frame, int layer, PN_stdfloat play_rate, PN_stdfloat blend_in) {
    pvector<AnimDef> anim_defs = get_anim_defs(channel, part_name, EMPTY_STR);
    
    for (size_t i = 0; i < anim_defs.size(); i++) {
        AnimDef anim_def = anim_defs[i];
        PT(Character) character = anim_def.get_character();
        if (character == nullptr) { continue; }
        
        // If no last frame is specified, We want the full animation.
        if (to_frame <= -1) {
            PT(AnimChannel) channel = anim_def.get_animation_channel();
            if (channel != nullptr) { 
                to_frame = channel->get_num_frames() - 1;
            } else {
                to_frame = 0;
            }
        }
        
        character->pingpong(anim_def.get_index(), restart, from_frame, to_frame, layer, anim_def.get_play_rate() * play_rate, blend_in);
    }
}

/**
 * pose(string, string, string, int=0, int=0, float=0.0, float=0.0)
 *
 * Pose the actor in position found at given frame in the specified
 * animation for the specified part. If no part is specified attempt
 * to apply pose to all parts.
**/
void CActor::pose(const std::string &anim_name, const std::string &part_name, const std::string &lod_name, int frame, int layer, PN_stdfloat blend_in, PN_stdfloat blend_out) {
    pvector<AnimDef> anim_defs = get_anim_defs(anim_name, part_name, lod_name);
    
    if (frame <= -1) { frame = 0; }
    
    for (size_t i = 0; i < anim_defs.size(); i++) {
        AnimDef anim_def = anim_defs[i];
        PT(Character) character = anim_def.get_character();
        if (character == nullptr) { continue; }
        
        character->pose(anim_def.get_index(), frame, layer, blend_in, blend_out);
    }
}

/**
 * pose(string, string, string, int=0, int=0, float=0.0, float=0.0)
 *
 * Pose the actor in position found at given frame in the specified
 * animation for the specified part. If no part is specified attempt
 * to apply pose to all parts.
**/
void CActor::pose(int channel, const std::string &part_name, const std::string &lod_name, int frame, int layer, PN_stdfloat blend_in, PN_stdfloat blend_out) {
    pvector<AnimDef> anim_defs = get_anim_defs(channel, part_name, lod_name);
    
    if (frame <= -1) { frame = 0; }
    
    for (size_t i = 0; i < anim_defs.size(); i++) {
        AnimDef anim_def = anim_defs[i];
        PT(Character) character = anim_def.get_character();
        if (character == nullptr) { continue; }
        
        character->pose(anim_def.get_index(), frame, layer, blend_in, blend_out);
    }
}

/**
 * set_transition(string, string, string, bool)
 *
 * Enables or disables transitions into the indicated animation.
**/
void CActor::set_transition(const std::string &anim_name, const std::string &part_name, const std::string &lod_name, bool flag) {
    pvector<AnimDef> anim_defs = get_anim_defs(anim_name, part_name, lod_name);
    
    for (size_t i = 0; i < anim_defs.size(); i++) {
        AnimDef anim_def = anim_defs[i];
        PT(AnimChannel) channel = anim_def.get_animation_channel();
        if (channel == nullptr) { continue; }
        
        if (flag) {
            channel->clear_flags(AnimChannel::F_snap);
        } else {
            channel->set_flags(AnimChannel::F_snap);
        }
    }
}

/**
 * set_transition(int, string, string, bool)
 *
 * Enables or disables transitions into the indicated animation.
**/
void CActor::set_transition(int channel, const std::string &part_name, const std::string &lod_name, bool flag) {
    pvector<AnimDef> anim_defs = get_anim_defs(channel, part_name, lod_name);
    
    for (size_t i = 0; i < anim_defs.size(); i++) {
        AnimDef anim_def = anim_defs[i];
        PT(AnimChannel) channel = anim_def.get_animation_channel();
        if (channel == nullptr) { continue; }
        
        if (flag) {
            channel->clear_flags(AnimChannel::F_snap);
        } else {
            channel->set_flags(AnimChannel::F_snap);
        }
    }
}


/**
 * load_anims(pvector<pair<string, string> >, string='modelRoot',
 * string='lodRoot', load_now=false)
 *
 * Actor anim loader. Takes an optional partName (defaults to
 * 'modelRoot' for non-multipart actors) and lodName (defaults
 * to 'lodRoot' for non-LOD actors) and map of corresponding
 * anims in the form animName:animPath
 * 
 * If load_now is true, the Actor will immediately load up all animations
 * from disk into memory.  Otherwise, animations will only be loaded the
 * first time they are accessed through the Actor.
**/
void CActor::load_anims(const pvector<std::pair<std::string, std::string> > &anims, const std::string &part_name, const std::string &lod_name, bool load_now) {
    pvector<std::string> lod_names;
    
    std::string anim_part_name("modelRoot");
    if (!part_name.empty()) { anim_part_name = part_name; }
    
    std::string anim_lod_name("lodRoot");
    if (!lod_name.empty()) { anim_lod_name = lod_name; }
    
    if (anims.size() == 0) {
        actor_cat.warning() << "Failed to load animations as no animations were passed!\n";
        return;
    }
    
    if (anim_lod_name.compare("all") == 0) {
        for (pmap<std::string, std::pair<int, int>>::iterator it = _switches.begin(); it != _switches.end(); it++) {
            lod_names.push_back(it->first);
        }
    } else {
        lod_names.push_back(anim_lod_name);
    }
    
    actor_cat.debug() << "in loadAnim: " << anims[0].first << ", part: " << anim_part_name << ", lod: " << lod_names[0] << '\n';
    
    for (size_t i = 0; i < anims.size(); i++) {
        std::pair<std::string, std::string> it = anims[i];
        std::string anim_name = it.first;
        std::string filename = it.second;
        
        if (!load_now) {
            // Just create an AnimDef that references no channel.
            // When we try to access the AnimDef it will load the channel
            // then and bind it.
            for (size_t i = 0; i < lod_names.size(); i++) {
                std::string l_name = lod_names[i];
                CActor::PartDef part_def = _part_bundle_dict[l_name + ":" + anim_part_name];
                PT(Character) character = part_def._character;
                CActor::AnimDef anim_def(filename, nullptr, character);
                anim_def.set_name(anim_name);
                part_def._anims_by_name[anim_name] = anim_def;
            }
        } else {
            // Load the channel into memory immediately and bind it.
            PT(AnimChannel) channel = load_anim(filename);
            if (channel == nullptr) { continue; }
            for (size_t i = 0; i < lod_names.size(); i++) {
                std::string l_name = lod_names[i];
                CActor::PartDef part_def = _part_bundle_dict[l_name + ":" + anim_part_name];
                PT(Character) character = part_def._character;
                CActor::AnimDef anim_def(filename, channel, character);
                anim_def.set_name(anim_name);
                part_def._anims_by_name[anim_name] = anim_def;
                if (!bind_anim(part_def, anim_def, channel)) {
                    actor_cat.warning() << "Failed to bind anim (" << anim_name << ", " << filename << ") to part " << anim_part_name << ", lod " << l_name << '\n';
                }
            }
        }
    }
}

/**
 * Loads a single animation from the indicated filename and returns the
 * AnimChannel contained within it.  Returns nullptr if an error occurred.
 * If the file contains multiple channels, it only returns the first one.
**/
AnimChannel *CActor::load_anim(const Filename &filename) {
    PT(PandaNode) anim_model = loader->load_sync(filename, LoaderOptions());
    if (anim_model == nullptr) {
        actor_cat.warning() << "Failed to load animation file " << filename << '\n';
        return nullptr;
    }
    
    NodePath anim_model_np = NodePath(anim_model);
    NodePath anim_bundle_np = anim_model_np.find("**/+AnimChannelBundle");
    if (anim_bundle_np.is_empty()) {
        actor_cat.warning() << "Model " << filename << " does not contain an animation!\n";
        return nullptr;
    }
    PT(AnimChannelBundle) anim_bundle_node = (AnimChannelBundle *)anim_bundle_np.node();
    // Add just the first channel within the bundle.
    // TODO: This will leave out other animations if there are multiple
    //       channels in the bundle.
    if (anim_bundle_node->get_num_channels() > 1) {
        actor_cat.warning() << "Channel bundle " << filename << " contains multiple channels, using only the first one\n";
    } else if (anim_bundle_node->get_num_channels() == 0) {
        actor_cat.warning() << "Channel bundle " << filename << " contains no channels!\n";
        return nullptr;
    }
    
    return anim_bundle_node->get_channel(0);
}

/**
 * Given an already loaded channel, binds the channel to the character
 * of the indicated part and stores the channel index on the indicated
 * AnimDef.  Returns true if the channel was successfully bound and
 * added to the part character, or false if there was an error.
**/
bool CActor::bind_anim(CActor::PartDef &part_def, CActor::AnimDef &anim_def, PT(AnimChannel) channel) {
    PT(Character) character = part_def._character;
    if (character == nullptr) { return false; }
    
    AnimChannelTable *animation_table = (AnimChannelTable *)channel.p();
    if (!character->bind_anim(animation_table)) {
        pmap<std::string, AnimDef>::iterator it = part_def._anims_by_name.find(anim_def.get_name());
        if (it != part_def._anims_by_name.end()) {
            part_def._anims_by_name.erase(it);
        }
        return false;
    }
    
    int channel_index = character->add_channel(channel);
    if (channel_index < 0) {
        pmap<std::string, AnimDef>::iterator it = part_def._anims_by_name.find(anim_def.get_name());
        if (it != part_def._anims_by_name.end()) {
            part_def._anims_by_name.erase(it);
        }
        return false;
    }
    
    anim_def.set_index(channel_index);
    anim_def.set_animation_channel(channel);
    part_def._anims_by_index[channel_index] = anim_def;
    
    return true;
}

/**
 * Loads up the AnimChannel at the filename specified by the AnimDef and
 * bind it to the Character of the PartDef.  Returns true on success, or
 * false if the animation could not be loaded or bound.
**/
bool CActor::load_and_bind_anim(CActor::PartDef &part_def, CActor::AnimDef &anim_def) {
    PT(AnimChannel) channel = load_anim(anim_def.get_filename());
    if (channel == nullptr) { return false; }
    
    return bind_anim(part_def, anim_def, channel);
}

/**
 * Actor model loader. Takes a model node (ie NodePath), a part
 * name(defaults to "modelRoot") and an lod name(defaults to "lodRoot").
**/
void CActor::load_model(const NodePath &model_node, const std::string &part_name, const std::string &lod_name, bool copy, bool ok_missing, bool keep_model) {
    NodePath model;
    
    std::string model_part_name("modelRoot");
    if (!part_name.empty()) { model_part_name = part_name; }
    
    std::string model_lod_name("lodRoot");
    if (!lod_name.empty()) { model_lod_name = lod_name; }
    
    actor_cat.debug() << "in loadModel: " << model_node.get_name() << ", part: " << model_part_name << ", lod: " << model_lod_name << ", copy: " << copy << '\n';
    
    if (copy) {
        model = model_node.copy_to(NodePath());
    } else {
        model = model_node;
    }
    
    load_model_internal(model, model_part_name, model_lod_name, copy, ok_missing, keep_model);
}

/**
 * Actor model loader. Takes a model name (ie file path), a part
 * name(defaults to "modelRoot") and an lod name(defaults to "lodRoot").
**/
void CActor::load_model(const std::string &model_path, const std::string &part_name, const std::string &lod_name, bool copy, bool ok_missing, bool keep_model) {
    NodePath model;
    
    std::string model_part_name("modelRoot");
    if (!part_name.empty()) { model_part_name = part_name; }
    
    std::string model_lod_name("lodRoot");
    if (!lod_name.empty()) { model_lod_name = lod_name; }
    
    actor_cat.debug() << "in loadModel: " << model_path << ", part: " << model_part_name << ", lod: " << model_lod_name << ", copy: " << copy << '\n';
    
    LoaderOptions loader_options = LoaderOptions(model_loader_options);
    if (!copy) {
        // If copy = false, then we should always hit the disk.
        loader_options.set_flags(loader_options.get_flags() & ~LoaderOptions::LF_no_ram_cache);
    }
    
    if (ok_missing) {
        loader_options.set_flags(loader_options.get_flags() & ~LoaderOptions::LF_report_errors);
    } else {
        loader_options.set_flags(loader_options.get_flags() | LoaderOptions::LF_report_errors);
    }
    
    // Pass loader_options to specify that we want to
    // get the skeleton model.  This only matters to model
    // files (like .mb) for which we can choose to extract
    // either the skeleton or animation, or neither.
    PT(PandaNode) node = loader->load_sync(Filename(model_path), loader_options);
    if (node != nullptr) {
        model = NodePath(node);
    } else {
        actor_cat.error() << "Could not load Actor model \"" << model_path << "\"!\n";
        return;
    }
    
    load_model_internal(model, model_part_name, model_lod_name, copy, ok_missing, keep_model);
}
    
void CActor::load_model_internal(NodePath &model, const std::string &part_name, const std::string &lod_name, bool copy, bool ok_missing, bool keep_model) {
     NodePath bundle_np, node_to_parent;
        
    if (model.node()->is_of_type(CharacterNode::get_class_type())) {
        bundle_np = model;
    } else {
        bundle_np = model.find("**/+CharacterNode");
    }
    
    if (bundle_np.is_empty()) {
        actor_cat.warning() << model.get_name() << " is not a character!\n";
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
    
    // Prepare our bundle for use.
    prepare_bundle(bundle_np, model, part_name, lod_name);
    
    // we rename this node to make Actor copying easier
    bundle_np.node()->set_name(part_prefix + part_name);
    
    // Check for channels embedded in the model.  If there are any, add
    // them to the PartDefs dictionary of channels so they are visible
    // to the Actor.  Channels embedded in the Character are assumed to
    // be already bound.
    std::string bundle_name = lod_name + ":" + part_name;
    pmap<std::string, CActor::PartDef>::iterator g = _part_bundle_dict.find(bundle_name);
    if (g == _part_bundle_dict.end()) {
        actor_cat.warning() << "Failed to find bundle " << bundle_name << " for channel setup!\n";
        return;
    }
    
    CActor::PartDef part_def = g->second;
    PT(Character) character = part_def._character;
    if (character == nullptr) {
        actor_cat.error() << "Character was NULL for " << bundle_name << " in channel setup!\n";
        return; 
    }
    
    int num_channels = character->get_num_channels();
    for (int i = 0; i < num_channels; i++) {
        PT(AnimChannel) channel = character->get_channel(i);
        AnimDef anim_def = AnimDef(Filename(), channel, character);
        std::string channel_name = std::string(channel->get_name());
        anim_def.set_name(channel_name);
        anim_def.set_index(i);
        part_def._anims_by_name[anim_def.get_name()] = anim_def;
        part_def._anims_by_index[i] = anim_def;
    }
}

void CActor::prepare_bundle(const NodePath &bundle_np, const NodePath &part_model, const std::string &part_name, const std::string &lod_name) {
    std::string bundle_name = lod_name + ":" + part_name;
    
    // Sanity check here just in case!
    if (!bundle_np.node()->is_of_type(CharacterNode::get_class_type())) {
        actor_cat.warning() << bundle_np.node()->get_name() << " is not a character! Failed to prepare bundle.\n";
        return;
    }
    
    // Make sure we have our name set.
    if (!_got_name) {
        this->node()->set_name(bundle_np.node()->get_name());
        _got_name = true;
    }
    
    // The original code would do a sort after this,
    // But pmaps do not need to be sorted.
    
    // We've checked beforehand that we're working with a character, Bundles are not
    // prepared otherwise.
    PT(CharacterNode) node = (CharacterNode *)bundle_np.node();
    
    // A model loaded from disk will always have just one bundle.
    //assert(node->get_num_bundles() == 1);
    
    // Get our character from the node we got.
    PT(Character) bundle_handle = node->get_character();
    
    CActor::PartDef part_def(bundle_np, bundle_handle, part_model);
    _part_bundle_dict[bundle_name] = part_def;
}

/**
 * set_lod_node(NodePath)
 * Set the node that switches actor geometry in and out.
 * If one is not supplied as an argument, make one.
**/
void CActor::set_lod_node(const NodePath &node) {
    // Sanity checks
    if (node.is_empty()) {
        actor_cat.warning() << "Failed to set LOD node, Node is empty!\n";
        return;
    }
    
    if (!node.node()->is_of_type(LODNode::get_class_type())) { 
        actor_cat.warning() << "Node " << node.node()->get_name() << " is not a LOD node! Failed to set LOD node.\n";
        return; 
    }
    
    // If we've already set our node before,
    // Then don't reset it.
    if (!_lod_node.is_empty()) {
        _lod_node = node;
    } else {
        _lod_node = _geom_node.attach_new_node(node.node());
        _has_LOD = true;
        _switches.clear();
    }
}

/**
 * add_lod(std::string, int, int)
 * Add a named node under the LODNode to parent all geometry
 * of a specific LOD under.
**/
void CActor::add_lod(const std::string &lod_name, int in_dist, int out_dist) {
    // Sanity check
    if (_lod_node.is_empty() || !_lod_node.node()->is_of_type(LODNode::get_class_type())) { return; }
    
    // Make sure we haven't already added this lod before.
    if (!get_lod(lod_name).is_empty()) { return; }
    
    _lod_node.attach_new_node(lod_name);
    // Save the switch distance info
    _switches[lod_name] = std::make_pair(in_dist, out_dist);
    // Add the switch distance info
    LODNode *lod_node = (LODNode *)_lod_node.node();
    lod_node->add_switch(in_dist, out_dist);
}

/**
 * add_lod(std::string, int, int, LPoint3f)
 * Add a named node under the LODNode to parent all geometry
 * of a specific LOD under.
**/
void CActor::add_lod(const std::string &lod_name, int in_dist, int out_dist, const LPoint3f &center) {
    // Sanity check
    if (_lod_node.is_empty() || !_lod_node.node()->is_of_type(LODNode::get_class_type())) { return; }
    
    // Make sure we haven't already added this lod before.
    if (!get_lod(lod_name).is_empty()) { return; }
    
    _lod_node.attach_new_node(lod_name);
    // Save the switch distance info
    _switches[lod_name] = std::make_pair(in_dist, out_dist);
    // Add the switch distance info
    LODNode *lod_node = (LODNode *)_lod_node.node();
    lod_node->add_switch(in_dist, out_dist);
    // Set our LOD center.
    set_center(center);
}

/**
 * set_lod(std::string, int, int)
 * Set the switch distance for given LOD
**/
void CActor::set_lod(const std::string &lod_name, int in_dist, int out_dist) {
    // Sanity check
    if (_lod_node.is_empty() || !_lod_node.node()->is_of_type(LODNode::get_class_type())) { return; }
    
    // Save the switch distance info
    _switches[lod_name] = std::make_pair(in_dist, out_dist);
    // Add the switch distance info
    LODNode *lod_node = (LODNode *)_lod_node.node();
    lod_node->set_switch(get_lod_index(lod_name), in_dist, out_dist);
}

/**
 * get_lod_index(std::string)
 * Safe method (but expensive) for retrieving the child index.
**/
int CActor::get_lod_index(const std::string &lod_name) {
    if (_lod_node.is_empty()) { return -1; }
    
    NodePath lod = get_lod(lod_name);
    if (lod.is_empty()) { return -1; }
    
    NodePathCollection children = _lod_node.get_children();
    
    for (int i = 0; i < children.get_num_paths(); i++) {
        NodePath path = children.get_path(i);
        if (path == lod) { return i; }
    }
    
    return -1;
}
        
/**
 * get_lod(std::string)
 * Get the named node under the LOD to which we parent all LOD
 * specific geometry to. Returns empty NodePath if not found.
**/
NodePath CActor::get_lod(const std::string &lod_name) {
    if (_lod_node.is_empty()) { return NodePath(); }
    
    NodePath lod = _lod_node.find(lod_name);
    if (lod.is_empty()) { return NodePath(); }
    
    return lod;
}


void CActor::set_center(const LPoint3f center) {
    _lod_center = center;
    
    // If we have no LOD node, Return.
    if (_lod_node.is_empty()) { return; }
    
    // Sanity check
    if (!_lod_node.node()->is_of_type(LODNode::get_class_type())) {
        actor_cat.warning() << _lod_node.node()->get_name() << " is not a LOD node! Failed to set a center for it.\n";
        return;
    }
    
    // Set our LOD nodes center.
    LODNode *lod_node = (LODNode *)_lod_node.node();
    lod_node->set_center(_lod_center);
    
    // In Python, set_lod_animation is called after this.
    // But it may as well be unused un-needed code.
    // self.__LODAnimation is completely un-needed
    // as set_lod_animation can just be called whenever you want.
}

/**
 * Returns a vector of AnimDefs for each part and lod combination for
 * the indicated anim_name (may also be a channel index).
**/
pvector<CActor::AnimDef> CActor::get_anim_defs(const std::string &anim_name) {
    pvector<AnimDef> anim_defs;
    pvector<PartDef> part_defs = get_part_defs();
    
    // We got our part defs, Need we need to iterate them all.
    for (size_t i = 0; i < part_defs.size(); i++) {
        PartDef part_def = part_defs[i];
        AnimDef *anim_def = part_def.get_anim_def(anim_name);
        if (anim_def != nullptr && (anim_def->is_bound() || load_and_bind_anim(part_def, *anim_def))) {
            anim_defs.push_back(*anim_def);
        }
    }
    
    return anim_defs;
}

/**
 * Returns a vector of AnimDefs for each part and lod combination for
 * the indicated anim_name (may also be a channel index).
**/
pvector<CActor::AnimDef> CActor::get_anim_defs(int anim_index) {
    pvector<AnimDef> anim_defs;
    pvector<PartDef> part_defs = get_part_defs();
    
    // We got our part defs, Need we need to iterate them all.
    for (size_t i = 0; i < part_defs.size(); i++) {
        PartDef part_def = part_defs[i];
        AnimDef *anim_def = part_def.get_anim_def(anim_index);
        if (anim_def != nullptr && (anim_def->is_bound() || load_and_bind_anim(part_def, *anim_def))) {
            anim_defs.push_back(*anim_def);
        }
    }
    
    return anim_defs;
}

/**
 * Returns a vector of AnimDefs for each part and lod combination for
 * the indicated anim_name (may also be a channel index).
**/
pvector<CActor::AnimDef> CActor::get_anim_defs(const std::string &anim_name, const std::string &part_name, const std::string &lod_name) {
    bool has_part_name = !part_name.empty();
    bool has_lod_name = !lod_name.empty();
    
    // If both strings are empty for some reason, Just call the version that needs no
    // paramaters.
    if (!has_part_name && !has_lod_name) { return get_anim_defs(anim_name); }
    
    pvector<AnimDef> anim_defs;
    pvector<PartDef> part_defs = get_part_defs(part_name, lod_name);
    
    // We got our part defs, Need we need to iterate them all.
    for (size_t i = 0; i < part_defs.size(); i++) {
        PartDef part_def = part_defs[i];
        AnimDef *anim_def = part_def.get_anim_def(anim_name);
        if (anim_def != nullptr && (anim_def->is_bound() || load_and_bind_anim(part_def, *anim_def))) {
            anim_defs.push_back(*anim_def);
        }
    }
    
    return anim_defs;
}

/**
 * Returns a vector of AnimDefs for each part and lod combination for
 * the indicated anim_name (may also be a channel index).
**/
pvector<CActor::AnimDef> CActor::get_anim_defs(int anim_index, const std::string &part_name, const std::string &lod_name) {
    bool has_part_name = !part_name.empty();
    bool has_lod_name = !lod_name.empty();
    
    // If both strings are empty for some reason, Just call the version that needs no
    // paramaters.
    if (!has_part_name && !has_lod_name) { return get_anim_defs(anim_index); }
    
    pvector<AnimDef> anim_defs;
    pvector<PartDef> part_defs = get_part_defs(part_name, lod_name);
    
    // We got our part defs, Need we need to iterate them all.
    for (size_t i = 0; i < part_defs.size(); i++) {
        PartDef part_def = part_defs[i];
        AnimDef *anim_def = part_def.get_anim_def(anim_index);
        if (anim_def != nullptr && (anim_def->is_bound() || load_and_bind_anim(part_def, *anim_def))) {
            anim_defs.push_back(*anim_def);
        }
    }
    
    return anim_defs;
}

/**
 * Returns a vector of AnimDefs for each part and lod combination for
 * the indicated anim_name (may also be a channel index).
**/
pvector<CActor::AnimDef> CActor::get_anim_defs(const std::string &anim_name, const pvector<std::string> &part_names, const std::string &lod_name) {
    bool has_part_names = part_names.size() <= 0;
    bool has_lod_name = !lod_name.empty();
    
    // If both our part name vector and lod name is empty for some reason, 
    // Just call the version that needs no paramaters.
    if (!has_part_names && !has_lod_name) { return get_anim_defs(anim_name); }
    
    pvector<AnimDef> anim_defs;
    pvector<PartDef> part_defs = get_part_defs(part_names, lod_name);
    
    // We got our part defs, Need we need to iterate them all.
    for (size_t i = 0; i < part_defs.size(); i++) {
        PartDef part_def = part_defs[i];
        AnimDef *anim_def = part_def.get_anim_def(anim_name);
        if (anim_def != nullptr && (anim_def->is_bound() || load_and_bind_anim(part_def, *anim_def))) {
            anim_defs.push_back(*anim_def);
        }
    }
    
    return anim_defs;
}

/**
 * Returns a vector of AnimDefs for each part and lod combination for
 * the indicated anim_name (may also be a channel index).
**/
pvector<CActor::AnimDef> CActor::get_anim_defs(int anim_index, const pvector<std::string> &part_names, const std::string &lod_name) {
    bool has_part_names = part_names.size() <= 0;
    bool has_lod_name = !lod_name.empty();
    
    // If both our part name vector and lod name is empty for some reason, 
    // Just call the version that needs no paramaters.
    if (!has_part_names && !has_lod_name) { return get_anim_defs(anim_index); }
    
    pvector<AnimDef> anim_defs;
    pvector<PartDef> part_defs = get_part_defs(part_names, lod_name);
    
    // We got our part defs, Need we need to iterate them all.
    for (size_t i = 0; i < part_defs.size(); i++) {
        PartDef part_def = part_defs[i];
        AnimDef *anim_def = part_def.get_anim_def(anim_index);
        if (anim_def != nullptr && (anim_def->is_bound() || load_and_bind_anim(part_def, *anim_def))) {
            anim_defs.push_back(*anim_def);
        }
    }
    
    return anim_defs;
}

/**
 * Returns a vector of PartDefs for each part and lod combination.
**/
pvector<CActor::PartDef> CActor::get_part_defs() {
    pvector<PartDef> part_defs;
    
    // Just iterate the entire map and get all of our PartDefs.
    for (pmap<std::string, PartDef>::iterator it = _part_bundle_dict.begin(); it != _part_bundle_dict.end(); it++) {
        PartDef part_def = it->second;
        part_defs.push_back(part_def);
    }
    
    return part_defs;
}

/**
 * Returns a vector of PartDefs for each part and lod combination.
**/
pvector<CActor::PartDef> CActor::get_part_defs(const std::string &part_name, const std::string &lod_name) {
    bool has_part_name = !part_name.empty();
    bool has_lod_name = !lod_name.empty();
    
    // If both strings are empty for some reason, Just call the version that needs no
    // paramaters.
    if (!has_part_name && !has_lod_name) { return get_part_defs(); }
    pvector<PartDef> part_defs;
    
    for (pmap<std::string, PartDef>::iterator it = _part_bundle_dict.begin(); it != _part_bundle_dict.end(); it++) {
        std::string curr_lod_name, curr_part_name;
        std::string bundle_name(it->first);
        PartDef part_def = it->second;
        
        // Get back both our lod name and our part name by splitting the string.
        curr_lod_name = bundle_name.substr(0, bundle_name.find(':'));
        // Erase the lod name and the delimiter.
        bundle_name.erase(0, bundle_name.find(':') + 1);
        // The bundle name is now the part name.
        curr_part_name = std::move(bundle_name);
        
        if (!has_lod_name) { // We want all part defs that match this part name, LOD or not.
            if (curr_part_name.compare(part_name) == 0) { part_defs.push_back(part_def); }
        } else if (!has_part_name) { // We want all part defs that are under this LOD.
            if (curr_lod_name.compare(lod_name) == 0) { part_defs.push_back(part_def); }
        } else { // We want all part defs that match this part name, and are under the specified LOD.
            if (curr_lod_name.compare(lod_name) == 0 && curr_part_name.compare(part_name) == 0) { part_defs.push_back(part_def); }
        }
    }
    
    return part_defs;
}

/**
 * Returns a vector of PartDefs for each part and lod combination.
**/
pvector<CActor::PartDef> CActor::get_part_defs(const pvector<std::string> &part_names, const std::string &lod_name) {
    bool has_part_names = part_names.size() <= 0;
    bool has_lod_name = !lod_name.empty();
    
    // If both our part name vector and lod name is empty for some reason, 
    // Just call the version that needs no paramaters.
    if (!has_part_names && !has_lod_name) { return get_part_defs(); }
    pvector<PartDef> part_defs;
    
    for (pmap<std::string, PartDef>::iterator it = _part_bundle_dict.begin(); it != _part_bundle_dict.end(); it++) {
        std::string curr_lod_name, curr_part_name;
        std::string bundle_name(it->first);
        PartDef part_def = it->second;
        
        // Get back both our lod name and our part name by splitting the string.
        curr_lod_name = bundle_name.substr(0, bundle_name.find(':'));
        // Erase the lod name and the delimiter.
        bundle_name.erase(0, bundle_name.find(':') + 1);
        // The bundle name is now the part name.
        curr_part_name = std::move(bundle_name);
        
        // If we don't have any part names, Then just check the lod name,
        // and continue the loop.
        if (!has_part_names) { // We want all part defs that are under this LOD.
            if (curr_lod_name.compare(lod_name) == 0) { part_defs.push_back(part_def); }
            continue;
        }
        
        // We have part names, So we need to iterate them all.
        for (size_t i = 0; i < part_names.size(); i++) {
            std::string part_name = part_names[i];
            
            // If we don't have a lod name, Only check the part name and continue the loop.
            if (!has_lod_name) { // We want all part defs that match this part name, LOD or not.
                if (curr_part_name.compare(part_name) == 0) { part_defs.push_back(part_def); }
                continue;
            }
            
            // We want all part defs that match this part name, and are under the specified LOD.
            if (curr_lod_name.compare(lod_name) == 0 && curr_part_name.compare(part_name) == 0) { part_defs.push_back(part_def); }
        }
    }
    
    return part_defs;
}

/**
 * Return the anim currently playing on the actor. If part not
 * specified return current anim of an arbitrary part in dictionary.
 * NOTE: Only returns info for an arbitrary LOD.
**/
std::string CActor::get_current_anim(int layer) {
    if (_part_bundle_dict.empty()) { return EMPTY_STR; }
    
    pmap<std::string, PartDef>::iterator it = _part_bundle_dict.begin();
    if (it == _part_bundle_dict.end()) { return EMPTY_STR; }
    
    std::string curr_lod_name, curr_part_name;
    std::string bundle_name(it->first);
    PartDef part_def = it->second;
    
    // Get back both our lod name and our part name by splitting the string.
    curr_lod_name = bundle_name.substr(0, bundle_name.find(':'));
    // Erase the lod name and the delimiter.
    bundle_name.erase(0, bundle_name.find(':') + 1);
    // The bundle name is now the part name.
    curr_part_name = std::move(bundle_name);
    
    // Return the animation playing on the indicated layer of the part.
    PT(Character) character = part_def._character;
    if (character == nullptr || !character->is_valid_layer_index(layer)) { return EMPTY_STR; }
    
    AnimLayer *anim_layer = character->get_anim_layer(layer);
    if (anim_layer == nullptr || !anim_layer->is_playing()) { return EMPTY_STR; }
    
    // Return the name associated with the channel index the layer is
    // playing.
    AnimDef anim_def = part_def._anims_by_index.at(anim_layer->_sequence);
    return anim_def.get_name();
}

/**
 * Return the anim currently playing on the actor. If part not
 * specified return current anim of an arbitrary part in dictionary.
 * NOTE: Only returns info for an arbitrary LOD.
**/
std::string CActor::get_current_anim(const std::string &part_name, int layer) {
    if (_part_bundle_dict.empty()) { return EMPTY_STR; }
    
    for (pmap<std::string, PartDef>::iterator it = _part_bundle_dict.begin(); it != _part_bundle_dict.end(); it++) {
        std::string curr_lod_name, curr_part_name;
        std::string bundle_name(it->first);
        PartDef part_def = it->second;
        
        // Get back both our lod name and our part name by splitting the string.
        curr_lod_name = bundle_name.substr(0, bundle_name.find(':'));
        // Erase the lod name and the delimiter.
        bundle_name.erase(0, bundle_name.find(':') + 1);
        // The bundle name is now the part name.
        curr_part_name = std::move(bundle_name);
        
        // If the part name doesn't match. Keep iterating.
        // If it doesn't exist at all, The loop will break out.
        if (curr_part_name.compare(part_name) != 0) { continue; }
        
        // Return the animation playing on the indicated layer of the part.
        PT(Character) character = part_def._character;
        if (character == nullptr || !character->is_valid_layer_index(layer)) { return EMPTY_STR; }
        
        AnimLayer *anim_layer = character->get_anim_layer(layer);
        if (anim_layer == nullptr || !anim_layer->is_playing()) { return EMPTY_STR; }
        
        // Return the name associated with the channel index the layer is
        // playing.
        AnimDef anim_def = part_def._anims_by_index.at(anim_layer->_sequence);
        return anim_def.get_name();
    }
    
    actor_cat.warning() << "No part named: " << part_name << '\n';
    return EMPTY_STR;
}

/**
 * Return the anim currently playing on the actor. If part not
 * specified return current anim of an arbitrary part in dictionary.
 * NOTE: Only returns info for an arbitrary LOD.
**/
int CActor::get_current_channel(int layer) {
    if (_part_bundle_dict.empty()) { return -1; }
    
    std::string working_part_name("modelRoot");
    
    for (pmap<std::string, PartDef>::iterator it = _part_bundle_dict.begin(); it != _part_bundle_dict.end(); it++) {
        std::string curr_lod_name, curr_part_name;
        std::string bundle_name(it->first);
        PartDef part_def = it->second;
        
        // Get back both our lod name and our part name by splitting the string.
        curr_lod_name = bundle_name.substr(0, bundle_name.find(':'));
        // Erase the lod name and the delimiter.
        bundle_name.erase(0, bundle_name.find(':') + 1);
        // The bundle name is now the part name.
        curr_part_name = std::move(bundle_name);
        
        // If the part name doesn't match. Keep iterating.
        // If it doesn't exist at all, The loop will break out.
        if (curr_part_name.compare(working_part_name) != 0) { continue; }
        
        PT(Character) character = part_def._character;
        if (character == nullptr || !character->is_valid_layer_index(layer)) { return -1; }
        
        AnimLayer *anim_layer = character->get_anim_layer(layer);
        if (anim_layer == nullptr || !anim_layer->is_playing()) { return -1; }
        
        return anim_layer->_sequence;
    }
    
    actor_cat.warning() << "No part named: modelRoot\n";
    return -1;
}

/**
 * Return the anim currently playing on the actor. If part not
 * specified return current anim of an arbitrary part in dictionary.
 * NOTE: Only returns info for an arbitrary LOD.
**/
int CActor::get_current_channel(const std::string &part_name, int layer) {
    if (_part_bundle_dict.empty()) { return -1; }
    
    std::string working_part_name("modelRoot");
    if (!part_name.empty()) { working_part_name = part_name; }
    
    for (pmap<std::string, PartDef>::iterator it = _part_bundle_dict.begin(); it != _part_bundle_dict.end(); it++) {
        std::string curr_lod_name, curr_part_name;
        std::string bundle_name(it->first);
        PartDef part_def = it->second;
        
        // Get back both our lod name and our part name by splitting the string.
        curr_lod_name = bundle_name.substr(0, bundle_name.find(':'));
        // Erase the lod name and the delimiter.
        bundle_name.erase(0, bundle_name.find(':') + 1);
        // The bundle name is now the part name.
        curr_part_name = std::move(bundle_name);
        
        // If the part name doesn't match. Keep iterating.
        // If it doesn't exist at all, The loop will break out.
        if (curr_part_name.compare(working_part_name) != 0) { continue; }
        
        PT(Character) character = part_def._character;
        if (character == nullptr || !character->is_valid_layer_index(layer)) { return -1; }
        
        AnimLayer *anim_layer = character->get_anim_layer(layer);
        if (anim_layer == nullptr || !anim_layer->is_playing()) { return -1; }
        
        return anim_layer->_sequence;
    }
    
    actor_cat.warning() << "No part named: " << working_part_name << '\n';
    return -1;
}

PN_stdfloat CActor::get_channel_length(int channel) {
    if (_part_bundle_dict.empty()) { return 0.1; }
    
    std::string working_part_name("modelRoot");
    
    for (pmap<std::string, PartDef>::iterator it = _part_bundle_dict.begin(); it != _part_bundle_dict.end(); it++) {
        std::string curr_lod_name, curr_part_name;
        std::string bundle_name(it->first);
        PartDef part_def = it->second;
        
        // Get back both our lod name and our part name by splitting the string.
        curr_lod_name = bundle_name.substr(0, bundle_name.find(':'));
        // Erase the lod name and the delimiter.
        bundle_name.erase(0, bundle_name.find(':') + 1);
        // The bundle name is now the part name.
        curr_part_name = std::move(bundle_name);
        
        // If the part name doesn't match. Keep iterating.
        // If it doesn't exist at all, The loop will break out.
        if (curr_part_name.compare(working_part_name) != 0) { continue; }
        
        PT(Character) character = part_def._character;
        if (character == nullptr || !character->is_valid_channel_index(channel)) { return 0.1; }
        
        AnimChannel *anim_channel = character->get_channel(channel);
        if (anim_channel == nullptr) { return 0.1; }
        
        return anim_channel->get_length(character);
    }
    
    actor_cat.warning() << "No part named: modelRoot\n";
    return 0.1;
}

PN_stdfloat CActor::get_channel_length(const std::string &part_name, int channel) {
    if (_part_bundle_dict.empty()) { return 0.1; }
    
    std::string working_part_name("modelRoot");
    if (!part_name.empty()) { working_part_name = part_name; }
    
    for (pmap<std::string, PartDef>::iterator it = _part_bundle_dict.begin(); it != _part_bundle_dict.end(); it++) {
        std::string curr_lod_name, curr_part_name;
        std::string bundle_name(it->first);
        PartDef part_def = it->second;
        
        // Get back both our lod name and our part name by splitting the string.
        curr_lod_name = bundle_name.substr(0, bundle_name.find(':'));
        // Erase the lod name and the delimiter.
        bundle_name.erase(0, bundle_name.find(':') + 1);
        // The bundle name is now the part name.
        curr_part_name = std::move(bundle_name);
        
        // If the part name doesn't match. Keep iterating.
        // If it doesn't exist at all, The loop will break out.
        if (curr_part_name.compare(working_part_name) != 0) { continue; }
        
        PT(Character) character = part_def._character;
        if (character == nullptr || !character->is_valid_channel_index(channel)) { return 0.1; }
        
        AnimChannel *anim_channel = character->get_channel(channel);
        if (anim_channel == nullptr) { return 0.1; }
        
        return anim_channel->get_length(character);
    }
    
    actor_cat.warning() << "No part named: " << working_part_name << '\n';
    return 0.1;
}

int CActor::get_channel_activity(int channel, int index) {
    if (_part_bundle_dict.empty()) { return -1; }
    
    std::string working_part_name("modelRoot");
    
    for (pmap<std::string, PartDef>::iterator it = _part_bundle_dict.begin(); it != _part_bundle_dict.end(); it++) {
        std::string curr_lod_name, curr_part_name;
        std::string bundle_name(it->first);
        PartDef part_def = it->second;
        
        // Get back both our lod name and our part name by splitting the string.
        curr_lod_name = bundle_name.substr(0, bundle_name.find(':'));
        // Erase the lod name and the delimiter.
        bundle_name.erase(0, bundle_name.find(':') + 1);
        // The bundle name is now the part name.
        curr_part_name = std::move(bundle_name);
        
        // If the part name doesn't match. Keep iterating.
        // If it doesn't exist at all, The loop will break out.
        if (curr_part_name.compare(working_part_name) != 0) { continue; }
        
        PT(Character) character = part_def._character;
        if (character == nullptr || !character->is_valid_channel_index(channel)) { return -1; }
        
        AnimChannel *anim_channel = character->get_channel(channel);
        if (anim_channel == nullptr || anim_channel->get_num_activities() == 0) { return -1; }
        
        return anim_channel->get_activity(index);
    }
    
    actor_cat.warning() << "No part named: modelRoot\n";
    return -1;
}

int CActor::get_channel_activity(const std::string &part_name, int channel, int index) {
    if (_part_bundle_dict.empty()) { return -1; }
    
    std::string working_part_name("modelRoot");
    if (!part_name.empty()) { working_part_name = part_name; }
    
    for (pmap<std::string, PartDef>::iterator it = _part_bundle_dict.begin(); it != _part_bundle_dict.end(); it++) {
        std::string curr_lod_name, curr_part_name;
        std::string bundle_name(it->first);
        PartDef part_def = it->second;
        
        // Get back both our lod name and our part name by splitting the string.
        curr_lod_name = bundle_name.substr(0, bundle_name.find(':'));
        // Erase the lod name and the delimiter.
        bundle_name.erase(0, bundle_name.find(':') + 1);
        // The bundle name is now the part name.
        curr_part_name = std::move(bundle_name);
        
        // If the part name doesn't match. Keep iterating.
        // If it doesn't exist at all, The loop will break out.
        if (curr_part_name.compare(working_part_name) != 0) { continue; }
        
        PT(Character) character = part_def._character;
        if (character == nullptr || !character->is_valid_channel_index(channel)) { return -1; }
        
        AnimChannel *anim_channel = character->get_channel(channel);
        if (anim_channel == nullptr || anim_channel->get_num_activities() == 0) { return -1; }
        
        return anim_channel->get_activity(index);
    }
    
    actor_cat.warning() << "No part named: " << working_part_name << '\n';
    return -1;
}

int CActor::get_channel_for_activity(int activity, int seed, int layer) {
    if (_part_bundle_dict.empty()) { return -1; }
    
    std::string working_part_name("modelRoot");
    
    for (pmap<std::string, PartDef>::iterator it = _part_bundle_dict.begin(); it != _part_bundle_dict.end(); it++) {
        int curr_channel = -1;
        std::string curr_lod_name, curr_part_name;
        std::string bundle_name(it->first);
        PartDef part_def = it->second;
        
        // Get back both our lod name and our part name by splitting the string.
        curr_lod_name = bundle_name.substr(0, bundle_name.find(':'));
        // Erase the lod name and the delimiter.
        bundle_name.erase(0, bundle_name.find(':') + 1);
        // The bundle name is now the part name.
        curr_part_name = std::move(bundle_name);
        
        // If the part name doesn't match. Keep iterating.
        // If it doesn't exist at all, The loop will break out.
        if (curr_part_name.compare(working_part_name) != 0) { continue; }
        
        PT(Character) character = part_def._character;
        if (character == nullptr) { return -1; }
        
        if (character->is_valid_layer_index(layer)) {
            AnimLayer *anim_layer = character->get_anim_layer(layer);
            curr_channel = anim_layer->_sequence;
        } 
        
        return character->get_channel_for_activity(activity, curr_channel, seed);
    }
    
    actor_cat.warning() << "No part named: modelRoot\n";
    return -1;
}

int CActor::get_channel_for_activity(const std::string &part_name, int activity, int seed, int layer) {
    if (_part_bundle_dict.empty()) { return -1; }
    
    std::string working_part_name("modelRoot");
    if (!part_name.empty()) { working_part_name = part_name; }
    
    for (pmap<std::string, PartDef>::iterator it = _part_bundle_dict.begin(); it != _part_bundle_dict.end(); it++) {
        int curr_channel = -1;
        std::string curr_lod_name, curr_part_name;
        std::string bundle_name(it->first);
        PartDef part_def = it->second;
        
        // Get back both our lod name and our part name by splitting the string.
        curr_lod_name = bundle_name.substr(0, bundle_name.find(':'));
        // Erase the lod name and the delimiter.
        bundle_name.erase(0, bundle_name.find(':') + 1);
        // The bundle name is now the part name.
        curr_part_name = std::move(bundle_name);
        
        // If the part name doesn't match. Keep iterating.
        // If it doesn't exist at all, The loop will break out.
        if (curr_part_name.compare(working_part_name) != 0) { continue; }
        
        PT(Character) character = part_def._character;
        if (character == nullptr) { return -1; }
        
        if (character->is_valid_layer_index(layer)) {
            AnimLayer *anim_layer = character->get_anim_layer(layer);
            curr_channel = anim_layer->_sequence;
        } 
        
        return character->get_channel_for_activity(activity, curr_channel, seed);
    }
    
    actor_cat.warning() << "No part named: " << working_part_name << '\n';
    return -1;
}

/**
 * Returns the current activity number of the indicated layer.
**/
int CActor::get_current_activity(int layer) {
    if (_part_bundle_dict.empty()) { return -1; }
    
    std::string working_part_name("modelRoot");
    
    for (pmap<std::string, PartDef>::iterator it = _part_bundle_dict.begin(); it != _part_bundle_dict.end(); it++) {
        std::string curr_lod_name, curr_part_name;
        std::string bundle_name(it->first);
        PartDef part_def = it->second;
        
        // Get back both our lod name and our part name by splitting the string.
        curr_lod_name = bundle_name.substr(0, bundle_name.find(':'));
        // Erase the lod name and the delimiter.
        bundle_name.erase(0, bundle_name.find(':') + 1);
        // The bundle name is now the part name.
        curr_part_name = std::move(bundle_name);
        
        // If the part name doesn't match. Keep iterating.
        // If it doesn't exist at all, The loop will break out.
        if (curr_part_name.compare(working_part_name) != 0) { continue; }
        
        PT(Character) character = part_def._character;
        if (character == nullptr || !character->is_valid_layer_index(layer)) { return -1; }
        
        AnimLayer *anim_layer = character->get_anim_layer(layer);
        if (anim_layer == nullptr) { return -1; }
        
        return anim_layer->_activity;
    }
    
    actor_cat.warning() << "No part named: modelRoot\n";
    return -1;
}

/**
 * Returns the current activity number of the indicated layer.
**/
int CActor::get_current_activity(const std::string &part_name, int layer) {
    if (_part_bundle_dict.empty()) { return -1; }
    
    std::string working_part_name("modelRoot");
    if (!part_name.empty()) { working_part_name = part_name; }
    
    for (pmap<std::string, PartDef>::iterator it = _part_bundle_dict.begin(); it != _part_bundle_dict.end(); it++) {
        std::string curr_lod_name, curr_part_name;
        std::string bundle_name(it->first);
        PartDef part_def = it->second;
        
        // Get back both our lod name and our part name by splitting the string.
        curr_lod_name = bundle_name.substr(0, bundle_name.find(':'));
        // Erase the lod name and the delimiter.
        bundle_name.erase(0, bundle_name.find(':') + 1);
        // The bundle name is now the part name.
        curr_part_name = std::move(bundle_name);
        
        // If the part name doesn't match. Keep iterating.
        // If it doesn't exist at all, The loop will break out.
        if (curr_part_name.compare(working_part_name) != 0) { continue; }
        
        PT(Character) character = part_def._character;
        if (character == nullptr || !character->is_valid_layer_index(layer)) { return -1; }
        
        AnimLayer *anim_layer = character->get_anim_layer(layer);
        if (anim_layer == nullptr) { return -1; }
        
        return anim_layer->_activity;
    }
    
    actor_cat.warning() << "No part named: " << working_part_name << '\n';
    return -1;
}

/**
 * Returns true if the channel playing on the indicated layer of the
 * indicated part has finished playing.
**/
bool CActor::is_current_channel_finished(int layer) {
    if (_part_bundle_dict.empty()) { return true; }
    
    std::string working_part_name("modelRoot");
    
    for (pmap<std::string, PartDef>::iterator it = _part_bundle_dict.begin(); it != _part_bundle_dict.end(); it++) {
        std::string curr_lod_name, curr_part_name;
        std::string bundle_name(it->first);
        PartDef part_def = it->second;
        
        // Get back both our lod name and our part name by splitting the string.
        curr_lod_name = bundle_name.substr(0, bundle_name.find(':'));
        // Erase the lod name and the delimiter.
        bundle_name.erase(0, bundle_name.find(':') + 1);
        // The bundle name is now the part name.
        curr_part_name = std::move(bundle_name);
        
        // If the part name doesn't match. Keep iterating.
        // If it doesn't exist at all, The loop will break out.
        if (curr_part_name.compare(working_part_name) != 0) { continue; }
        
        PT(Character) character = part_def._character;
        if (character == nullptr || !character->is_valid_layer_index(layer)) { return true; }
        
        AnimLayer *anim_layer = character->get_anim_layer(layer);
        if (anim_layer == nullptr) { return true; }
        
        return anim_layer->_sequence_finished;
    }
    
    actor_cat.warning() << "No part named: modelRoot\n";
    return true;
}

/**
 * Returns true if the channel playing on the indicated layer of the
 * indicated part has finished playing.
**/
bool CActor::is_current_channel_finished(const std::string &part_name, int layer) {
    if (_part_bundle_dict.empty()) { return true; }
    
    std::string working_part_name("modelRoot");
    if (!part_name.empty()) { working_part_name = part_name; }
    
    for (pmap<std::string, PartDef>::iterator it = _part_bundle_dict.begin(); it != _part_bundle_dict.end(); it++) {
        std::string curr_lod_name, curr_part_name;
        std::string bundle_name(it->first);
        PartDef part_def = it->second;
        
        // Get back both our lod name and our part name by splitting the string.
        curr_lod_name = bundle_name.substr(0, bundle_name.find(':'));
        // Erase the lod name and the delimiter.
        bundle_name.erase(0, bundle_name.find(':') + 1);
        // The bundle name is now the part name.
        curr_part_name = std::move(bundle_name);
        
        // If the part name doesn't match. Keep iterating.
        // If it doesn't exist at all, The loop will break out.
        if (curr_part_name.compare(working_part_name) != 0) { continue; }
        
        PT(Character) character = part_def._character;
        if (character == nullptr || !character->is_valid_layer_index(layer)) { return true; }
        
        AnimLayer *anim_layer = character->get_anim_layer(layer);
        if (anim_layer == nullptr) { return true; }
        
        return anim_layer->_sequence_finished;
    }
    
    actor_cat.warning() << "No part named: " << working_part_name << '\n';
    return true;
}

/**
 * Returns true if the indicated layer of the indicated part is currently
 * playing a channel.
**/
bool CActor::is_channel_playing(int layer) {
    if (_part_bundle_dict.empty()) { return false; }
    
    std::string working_part_name("modelRoot");
    
    for (pmap<std::string, PartDef>::iterator it = _part_bundle_dict.begin(); it != _part_bundle_dict.end(); it++) {
        std::string curr_lod_name, curr_part_name;
        std::string bundle_name(it->first);
        PartDef part_def = it->second;
        
        // Get back both our lod name and our part name by splitting the string.
        curr_lod_name = bundle_name.substr(0, bundle_name.find(':'));
        // Erase the lod name and the delimiter.
        bundle_name.erase(0, bundle_name.find(':') + 1);
        // The bundle name is now the part name.
        curr_part_name = std::move(bundle_name);
        
        // If the part name doesn't match. Keep iterating.
        // If it doesn't exist at all, The loop will break out.
        if (curr_part_name.compare(working_part_name) != 0) { continue; }
        
        PT(Character) character = part_def._character;
        if (character == nullptr || !character->is_valid_layer_index(layer)) { return false; }
        
        AnimLayer *anim_layer = character->get_anim_layer(layer);
        if (anim_layer == nullptr) { return false; }
        
        return anim_layer->is_playing();
    }
    
    actor_cat.warning() << "No part named: modelRoot\n";
    return false;
}

/**
 * Returns true if the indicated layer of the indicated part is currently
 * playing a channel.
**/
bool CActor::is_channel_playing(const std::string &part_name, int layer) {
    if (_part_bundle_dict.empty()) { return false; }
    
    std::string working_part_name("modelRoot");
    if (!part_name.empty()) { working_part_name = part_name; }
    
    for (pmap<std::string, PartDef>::iterator it = _part_bundle_dict.begin(); it != _part_bundle_dict.end(); it++) {
        std::string curr_lod_name, curr_part_name;
        std::string bundle_name(it->first);
        PartDef part_def = it->second;
        
        // Get back both our lod name and our part name by splitting the string.
        curr_lod_name = bundle_name.substr(0, bundle_name.find(':'));
        // Erase the lod name and the delimiter.
        bundle_name.erase(0, bundle_name.find(':') + 1);
        // The bundle name is now the part name.
        curr_part_name = std::move(bundle_name);
        
        // If the part name doesn't match. Keep iterating.
        // If it doesn't exist at all, The loop will break out.
        if (curr_part_name.compare(working_part_name) != 0) { continue; }
        
        PT(Character) character = part_def._character;
        if (character == nullptr || !character->is_valid_layer_index(layer)) { return false; }
        
        AnimLayer *anim_layer = character->get_anim_layer(layer);
        if (anim_layer == nullptr) { return false; }
        
        return anim_layer->is_playing();
    }
    
    actor_cat.warning() << "No part named: " << working_part_name << '\n';
    return false;
}

/**
 * Returns the current cycle of the channel playing on the indicated layer
 * of the indicated part.
**/
PN_stdfloat CActor::get_cycle(int layer) {
    if (_part_bundle_dict.empty()) { return 0.0; }
    
    std::string working_part_name("modelRoot");
    
    for (pmap<std::string, PartDef>::iterator it = _part_bundle_dict.begin(); it != _part_bundle_dict.end(); it++) {
        std::string curr_lod_name, curr_part_name;
        std::string bundle_name(it->first);
        PartDef part_def = it->second;
        
        // Get back both our lod name and our part name by splitting the string.
        curr_lod_name = bundle_name.substr(0, bundle_name.find(':'));
        // Erase the lod name and the delimiter.
        bundle_name.erase(0, bundle_name.find(':') + 1);
        // The bundle name is now the part name.
        curr_part_name = std::move(bundle_name);
        
        // If the part name doesn't match. Keep iterating.
        // If it doesn't exist at all, The loop will break out.
        if (curr_part_name.compare(working_part_name) != 0) { continue; }
        
        PT(Character) character = part_def._character;
        if (character == nullptr || !character->is_valid_layer_index(layer)) { return 0.0; }
        
        AnimLayer *anim_layer = character->get_anim_layer(layer);
        if (anim_layer == nullptr) { return 0.0; }
        
        return anim_layer->_cycle;
    }
    
    actor_cat.warning() << "No part named: modelRoot\n";
    return 0.0;
}

/**
 * Returns the current cycle of the channel playing on the indicated layer
 * of the indicated part.
**/
PN_stdfloat CActor::get_cycle(const std::string &part_name, int layer) {
    if (_part_bundle_dict.empty()) { return 0.0; }
    
    std::string working_part_name("modelRoot");
    if (!part_name.empty()) { working_part_name = part_name; }
    
    for (pmap<std::string, PartDef>::iterator it = _part_bundle_dict.begin(); it != _part_bundle_dict.end(); it++) {
        std::string curr_lod_name, curr_part_name;
        std::string bundle_name(it->first);
        PartDef part_def = it->second;
        
        // Get back both our lod name and our part name by splitting the string.
        curr_lod_name = bundle_name.substr(0, bundle_name.find(':'));
        // Erase the lod name and the delimiter.
        bundle_name.erase(0, bundle_name.find(':') + 1);
        // The bundle name is now the part name.
        curr_part_name = std::move(bundle_name);
        
        // If the part name doesn't match. Keep iterating.
        // If it doesn't exist at all, The loop will break out.
        if (curr_part_name.compare(working_part_name) != 0) { continue; }
        
        PT(Character) character = part_def._character;
        if (character == nullptr || !character->is_valid_layer_index(layer)) { return 0.0; }
        
        AnimLayer *anim_layer = character->get_anim_layer(layer);
        if (anim_layer == nullptr) { return 0.0; }
        
        return anim_layer->_cycle;
    }
    
    actor_cat.warning() << "No part named: " << working_part_name << '\n';
    return 0.0;
}

/**
 * Return the current frame number of the named animation, or if no
 * animation is specified, then the animation current playing on the
 * actor. If part not specified return current animation of first part
 * in dictionary.
 * NOTE: Only returns info for an arbitrary LOD.
**/
int CActor::get_current_frame(int layer) {
    if (_part_bundle_dict.empty()) { return 0; }
    
    // Get the first entry.
    pmap<std::string, PartDef>::iterator it = _part_bundle_dict.begin();
    if (it == _part_bundle_dict.end()) { return 0; }
    
    // Get the part definition from our iterator.
    PartDef part_def = it->second;
    
    // Get our character and sanity check our layer.
    PT(Character) character = part_def._character;
    if (character == nullptr || !character->is_valid_layer_index(layer)) { return 0; }
    
    // Get our animation layer, And make sure it's playing.
    AnimLayer *anim_layer = character->get_anim_layer(layer);
    if (anim_layer == nullptr || !anim_layer->is_playing()) { return 0; }
    
    // Make sure the channel is valid.
    if (!character->is_valid_channel_index(anim_layer->_sequence)) { return 0; }
    
    // Get the animation channel.
    PT(AnimChannel) channel = character->get_channel(anim_layer->_sequence);
    if (channel == nullptr) { return 0; }
    
    // Return our current frame.
    return (anim_layer->_cycle * (channel->get_num_frames() - 1));
}

/**
 * Return the current frame number of the named animation, or if no
 * animation is specified, then the animation current playing on the
 * actor. If part not specified return current animation of first part
 * in dictionary.
 * NOTE: Only returns info for an arbitrary LOD.
**/
int CActor::get_current_frame(const std::string &part_name, int layer) {
    if (_part_bundle_dict.empty()) { return 0; }
    
    std::string working_part_name("modelRoot");
    if (!part_name.empty()) { working_part_name = part_name; }
    
    for (pmap<std::string, PartDef>::iterator it = _part_bundle_dict.begin(); it != _part_bundle_dict.end(); it++) {
        std::string curr_lod_name, curr_part_name;
        
        // Get the bundle name from our iterator.
        std::string bundle_name(it->first);
        
        // Get the part definition from our iterator.
        PartDef part_def = it->second;
        
        // Get back both our lod name and our part name by splitting the string.
        curr_lod_name = bundle_name.substr(0, bundle_name.find(':'));
        // Erase the lod name and the delimiter.
        bundle_name.erase(0, bundle_name.find(':') + 1);
        // The bundle name is now the part name.
        curr_part_name = std::move(bundle_name);
        
        // If the part name doesn't match. Keep iterating.
        // If it doesn't exist at all, The loop will break out.
        if (curr_part_name.compare(working_part_name) != 0) { continue; }
        
        // Get our character and sanity check our layer.
        PT(Character) character = part_def._character;
        if (character == nullptr || !character->is_valid_layer_index(layer)) { return 0; }
        
        // Get our animation layer, And make sure it's playing.
        AnimLayer *anim_layer = character->get_anim_layer(layer);
        if (anim_layer == nullptr || !anim_layer->is_playing()) { return 0; }
        
        // Make sure the channel is valid.
        if (!character->is_valid_channel_index(anim_layer->_sequence)) { return 0; }
        
        // Get the animation channel.
        PT(AnimChannel) channel = character->get_channel(anim_layer->_sequence);
        if (channel == nullptr) { return 0; }
        
        // Return our current frame.
        return (anim_layer->_cycle * (channel->get_num_frames() - 1));
    }
    
    actor_cat.warning() << "Couldn't find part: " << working_part_name << '\n';
    return 0;
}

/**
 * Return the current frame number of the named animation, or if no
 * animation is specified, then the animation current playing on the
 * actor. If part not specified return current animation of first part
 * in dictionary.
 * NOTE: Only returns info for an arbitrary LOD.
**/
int CActor::get_current_frame(const std::string &anim_name, const std::string &part_name, int layer) {
    if (_part_bundle_dict.empty()) { return 0; }
    
    std::string working_part_name("modelRoot");
    if (!part_name.empty()) { working_part_name = part_name; }
    
    // If the animation name is empty, Call the version of this function which only needs a part name.
    if (anim_name.empty()) { return get_current_frame(part_name, layer); }
    
    // Get all of our animation definitions.
    pvector<AnimDef> anim_defs = get_anim_defs(anim_name, part_name, EMPTY_STR);
    if (anim_defs.empty()) { return 0; }
    
    // Return current frame of the named animation if it is currently
    // playing on any layer.
    JobSystem *jsys = JobSystem::get_global_ptr();
    jsys->parallel_process(anim_defs.size(), [&] (size_t i) { //for (size_t i = 0; i < anim_defs.size(); i++) {
        AnimDef anim_def = anim_defs[i];
        
        // Get our character and sanity check our layer.
        PT(Character) character = anim_def.get_character();
        if (character == nullptr) { return 0; }
        
        // Get the animation channel.
        PT(AnimChannel) channel = anim_def.get_animation_channel();
        if (channel == nullptr) { return 0; }
        
        // Find the layer playing the channel.
        for (int i = 0; i < character->get_num_anim_layers(); i++) {
            AnimLayer *anim_layer = character->get_anim_layer(i);
            
            // Make sure the animation layer is playing.
            if (anim_layer == nullptr || !anim_layer->is_playing()) { continue; }
            
            // If the animation layer channel index and the animation definition channel index
            // don't match, Continue onward.
            if (anim_layer->_sequence != anim_def.get_index()) { continue; }
            
            // Return our current frame.
            return (int)(anim_layer->_cycle * (channel->get_num_frames() - 1));
        }
    });
    
    // No matches found, Return 0.
    return 0;
}

/**
 * Advances the animation time on all layers of the indicated part, or all
 * parts if no part is specified.
**/
void CActor::advance() {
    pvector<PT(Character)> bundles = get_part_bundles();
    
    JobSystem *jsys = JobSystem::get_global_ptr();
    jsys->parallel_process(bundles.size(), [&] (size_t i) { //for (size_t i = 0; i < bundles.size(); i++) {
        PT(Character) character = bundles[i];
        character->advance();
    });
}

/**
 * Advances the animation time on all layers of the indicated part, or all
 * parts if no part is specified.
**/
void CActor::advance(const std::string &part_name) {
    pvector<PT(Character)> bundles = get_part_bundles(part_name);
    
    JobSystem *jsys = JobSystem::get_global_ptr();
    jsys->parallel_process(bundles.size(), [&] (size_t i) { //for (size_t i = 0; i < bundles.size(); i++) {
        PT(Character) character = bundles[i];
        character->advance();
    });
}

void CActor::set_auto_advance(bool flag) {
    pvector<PT(Character)> bundles = get_part_bundles();
    
    JobSystem *jsys = JobSystem::get_global_ptr();
    jsys->parallel_process(bundles.size(), [&] (size_t i) { //for (size_t i = 0; i < bundles.size(); i++) {
        PT(Character) character = bundles[i];
        character->set_auto_advance_flag(flag);
    });
}

void CActor::set_auto_advance(const std::string &part_name, bool flag) {
    pvector<PT(Character)> bundles = get_part_bundles(part_name);
    
    JobSystem *jsys = JobSystem::get_global_ptr();
    jsys->parallel_process(bundles.size(), [&] (size_t i) { //for (size_t i = 0; i < bundles.size(); i++) {
        PT(Character) character = bundles[i];
        character->set_auto_advance_flag(flag);
    });
}

/**
 * Changes the way the Actor handles blending of multiple
 * different animations, and/or interpolation between consecutive
 * frames.
 * 
 * The frame_blend and transition_blend parameters are boolean flags.
 * You may set either or both to true or false.
 * 
 * The frame_blend flag is unrelated to playing multiple
 * animations.  It controls whether the Actor smoothly
 * interpolates between consecutive frames of its animation (when
 * the flag is true) or holds each frame until the next one is
 * ready (when the flag is false).  The default value of
 * frame_blend is controlled by the interpolate-frames Config.prc
 * variable.
**/
void CActor::set_blend(bool frame_blend, bool transition_blend) {
    pvector<PT(Character)> bundles = get_part_bundles();
    
    JobSystem *jsys = JobSystem::get_global_ptr();
    jsys->parallel_process(bundles.size(), [&] (size_t i) { //for (size_t i = 0; i < bundles.size(); i++) {
        PT(Character) character = bundles[i];
        character->set_frame_blend_flag(frame_blend);
        character->set_channel_transition_flag(transition_blend);
    });
}

/**
 * Changes the way the Actor handles blending of multiple
 * different animations, and/or interpolation between consecutive
 * frames.
 * 
 * The frame_blend and transition_blend parameters are boolean flags.
 * You may set either or both to true or false.
 * 
 * The frame_blend flag is unrelated to playing multiple
 * animations.  It controls whether the Actor smoothly
 * interpolates between consecutive frames of its animation (when
 * the flag is true) or holds each frame until the next one is
 * ready (when the flag is false).  The default value of
 * frame_blend is controlled by the interpolate-frames Config.prc
 * variable.
**/
void CActor::set_blend(const std::string &part_name, bool frame_blend, bool transition_blend) {
    pvector<PT(Character)> bundles = get_part_bundles(part_name);
    
    JobSystem *jsys = JobSystem::get_global_ptr();
    jsys->parallel_process(bundles.size(), [&] (size_t i) { //for (size_t i = 0; i < bundles.size(); i++) {
        PT(Character) character = bundles[i];
        character->set_frame_blend_flag(frame_blend);
        character->set_channel_transition_flag(transition_blend);
    });
}

/**
 * Returns a vector of characters for the entire Actor,
 * or for the indicated part only.
**/
pvector<PT(Character)> CActor::get_part_bundles() {
    pvector<PT(Character)> part_bundles;
    
    for (pmap<std::string, PartDef>::iterator it = _part_bundle_dict.begin(); it != _part_bundle_dict.end(); it++) {
        // Get the part definition from our iterator.
        PartDef part_def = it->second;
        
        // Get our character, and if it's a nullptr; Continue as if nothing happened.
        PT(Character) character = part_def._character;
        if (character == nullptr) { continue; }
        
        part_bundles.push_back(character);
    }
    
    return part_bundles;
}

/**
 * Returns a vector of characters for the entire Actor,
 * or for the indicated part only.
**/
pvector<PT(Character)> CActor::get_part_bundles(const std::string &part_name) {
    pvector<PT(Character)> part_bundles;
    
    std::string working_part_name("modelRoot");
    if (!part_name.empty()) { working_part_name = part_name; }
    
    for (pmap<std::string, PartDef>::iterator it = _part_bundle_dict.begin(); it != _part_bundle_dict.end(); it++) {
        std::string curr_lod_name, curr_part_name;
        
        // Get the bundle name from our iterator.
        std::string bundle_name(it->first);
        
        // Get the part definition from our iterator.
        PartDef part_def = it->second;
        
        // Get back both our lod name and our part name by splitting the string.
        curr_lod_name = bundle_name.substr(0, bundle_name.find(':'));
        // Erase the lod name and the delimiter.
        bundle_name.erase(0, bundle_name.find(':') + 1);
        // The bundle name is now the part name.
        curr_part_name = std::move(bundle_name);
        
        // If the part name doesn't match. Keep iterating.
        // If it doesn't exist at all, The loop will break out.
        if (curr_part_name.compare(working_part_name) != 0) { continue; }
        
        // Get our character, and if it's a nullptr; Continue as if nothing happened.
        PT(Character) character = part_def._character;
        if (character == nullptr) { continue; }
        
        part_bundles.push_back(character);
    }
    
    // We couldn't find the specified part.
    if (part_bundles.empty()) { actor_cat.warning() << "Couldn't find part: " << working_part_name << '\n'; }
    
    return part_bundles;
}

void CActor::list_joints(const std::string &part_name, const std::string &lod_name) {
    std::string working_part_name("modelRoot");
    if (!part_name.empty()) { working_part_name = part_name; }
    
    std::string working_lod_name("lodRoot");
    if (!lod_name.empty()) { working_lod_name = lod_name; }
    
    for (pmap<std::string, PartDef>::iterator it = _part_bundle_dict.begin(); it != _part_bundle_dict.end(); it++) {
        std::string curr_lod_name, curr_part_name;
        
        // Get the bundle name from our iterator.
        std::string bundle_name(it->first);
        
        // Get the part definition from our iterator.
        PartDef part_def = it->second;
        
        // Get back both our lod name and our part name by splitting the string.
        curr_lod_name = bundle_name.substr(0, bundle_name.find(':'));
        // Erase the lod name and the delimiter.
        bundle_name.erase(0, bundle_name.find(':') + 1);
        // The bundle name is now the part name.
        curr_part_name = std::move(bundle_name);
        
        // If the part name or lod name doesn't match. Keep iterating.
        // If it doesn't exist at all, The loop will break out.
        if (curr_lod_name.compare(working_lod_name) != 0 || curr_part_name.compare(working_part_name) != 0) { continue; }
        
        // Get our character, and if it's a nullptr; Break as we can no longer list the joints.
        PT(Character) character = part_def._character;
        if (character == nullptr) { break; }
        
        // Get the joint list.
        std::stringstream ss;
        do_list_joints(ss, character, 0, 0);
        
        // Output the joint list.
        std::cout << ss.str() << std::endl;
    }
}

void CActor::do_list_joints(std::stringstream &ss, PT(Character) character, int indent_level, int joint) {
    const std::string &joint_name = character->get_joint_name(joint);
    LMatrix4 joint_value = character->get_joint_value(joint);
    
    // Write our joint info to our stream.
    ss << ' ' * indent_level << joint_name << ' ' << TransformState::make_mat(joint_value) << '\n';
    
    // Iterate all of the joints children.
    for (int i = 0; i < character->get_joint_num_children(joint); i++) {
        do_list_joints(ss, character, indent_level + 2, character->get_joint_child(joint, i));
    }
}

const Filename CActor::get_anim_filename(const std::string &anim_name, const std::string &part_name) {
    std::string working_part_name("modelRoot");
    if (!part_name.empty()) { working_part_name = part_name; }
    
    for (pmap<std::string, PartDef>::iterator it = _part_bundle_dict.begin(); it != _part_bundle_dict.end(); it++) {
        std::string curr_lod_name, curr_part_name;
        
        // Get the bundle name from our iterator.
        std::string bundle_name(it->first);
        
        // Get the part definition from our iterator.
        PartDef part_def = it->second;
        
        // Get back both our lod name and our part name by splitting the string.
        curr_lod_name = bundle_name.substr(0, bundle_name.find(':'));
        // Erase the lod name and the delimiter.
        bundle_name.erase(0, bundle_name.find(':') + 1);
        // The bundle name is now the part name.
        curr_part_name = std::move(bundle_name);
        
        // If the part name doesn't match. Keep iterating.
        // If it doesn't exist at all, The loop will break out.
        if (curr_part_name.compare(working_part_name) != 0) { continue; }
        
        // Get our animation definition.
        AnimDef *anim_def = part_def.get_anim_def(anim_name);
        if (anim_def == nullptr) { return Filename(); }
        
        return anim_def->get_filename();
    }
    
    return Filename();
}

/**
 * No-op.
**/
void CActor::post_flatten() {
}


/* Part Defitition */

int CActor::PartDef::get_channel_index(const std::string &anim_name) {
    pmap<std::string, AnimDef>::iterator g = _anims_by_name.find(anim_name);
    if (g == _anims_by_name.end()) {
        actor_cat.warning() << "No animation named: " << anim_name << '\n';
        return -1;
    }
    return g->second.get_index();
}

CActor::AnimDef *CActor::PartDef::get_anim_def(int index) {
    if (index >= _anims_by_index.size() || index <= -1) {
        actor_cat.warning() << "Invalid animation index: " << index << '\n';
        return nullptr;
    }
    return &_anims_by_index[index];
}

CActor::AnimDef *CActor::PartDef::get_anim_def(const std::string &anim_name) {
    pmap<std::string, AnimDef>::iterator g = _anims_by_name.find(anim_name);
    if (g == _anims_by_name.end()) {
        actor_cat.warning() << "No animation named: " << anim_name << '\n';
        return nullptr;
    }
    return &g->second;
}