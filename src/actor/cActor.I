/* Actor */

/**
 * Loads a single animation from the indicated filename and returns the
 * AnimChannel contained within it.  Returns nullptr if an error occurred.
 * If the file contains multiple channels, it only returns the first one.
**/
INLINE AnimChannel *CActor::load_anim(const std::string &filename) {
    Filename file(filename);
    return load_anim(file);
}

/**
 * set_geom_node()
**/
INLINE void CActor::set_geom_node(const NodePath &node) {
    _geom_node = node;
}

/**
 * get_geom_node()
 * Returns a reference to the geom NodePath.
**/
INLINE NodePath &CActor::get_geom_node() {
    return _geom_node;
}

/**
 * get_geom_node()
 * Returns a constant reference to the geom NodePath.
 *
 * ONLY USED INTERNALLY.
**/
INLINE const NodePath &CActor::get_geom_node() const {
    return _geom_node;
}

/**
 * set_lod_node()
 * Set the node that switches actor geometry in and out.
 * If one is not supplied as an argument, make one.
**/
INLINE void CActor::set_lod_node() {
    PT(LODNode) node = LODNode::make_default_lod("lod");
    NodePath nodepath(node);
    set_lod_node(nodepath);
}

/**
 * Return the node that switches actor geometry in and out.
**/
INLINE LODNode *CActor::get_lod_node() {
    if (_lod_node.is_empty() || !_lod_node.node()->is_of_type(LODNode::get_class_type())) { return nullptr; }
    
    return (LODNode *)_lod_node.node();
}

INLINE void CActor::use_lod(const std::string &lod_name) {
    // Sanity check
    if (_lod_node.is_empty() || !_lod_node.node()->is_of_type(LODNode::get_class_type())) { return; }
    
    NodePath child = _lod_node.find(lod_name);
    // Make sure the child isn't a empty node.
    if (child.is_empty()) { return; }
    
    LODNode *lod_node = (LODNode *)_lod_node.node();
    int index = lod_node->find_child(child.node());
    lod_node->force_switch(index);
}

/**
 * Restore all switch distance info (usually after a use_lod call)
**/
INLINE void CActor::reset_lod() {
    // Sanity check
    if (_lod_node.is_empty() || !_lod_node.node()->is_of_type(LODNode::get_class_type())) { return; }
    
    // Set our LOD nodes center.
    LODNode *lod_node = (LODNode *)_lod_node.node();
    lod_node->clear_force_switch();
}

/**
 * Return true if the actor has LODs, false otherwise.
**/
INLINE bool CActor::has_lod() {
    return _has_LOD;
}

INLINE void CActor::face_away_from_viewer() {
    NodePath &geom_node = get_geom_node();
    geom_node.set_h(180);
}

INLINE void CActor::face_towards_viewer() {
    NodePath &geom_node = get_geom_node();
    geom_node.set_h(0);
}

INLINE const pmap<std::string, CActor::PartDef> &CActor::get_part_bundle_dict() const {
    return _part_bundle_dict;
}

INLINE void CActor::list_joints() {
    list_joints("", "");
}

INLINE const Filename CActor::get_anim_filename(const std::string &anim_name) {
    return get_anim_filename(anim_name, "");
}


/* Animation Defitition */

INLINE CActor::AnimDef::AnimDef(Filename filename, PT(AnimChannel) channel, PT(Character) character) : _filename(filename) {
    _channel = channel;
    _character = character;
}

INLINE void CActor::AnimDef::set_filename(const std::string &filename) {
    _filename = Filename(filename);
}

INLINE void CActor::AnimDef::set_filename(const Filename &filename) {
    _filename = filename;
}

INLINE const Filename &CActor::AnimDef::get_filename() {
    return _filename;
}

INLINE void CActor::AnimDef::set_animation_channel(AnimChannel *channel) {
    _channel = channel;
}

INLINE PT(AnimChannel) CActor::AnimDef::get_animation_channel() {
    return _channel;
}

INLINE void CActor::AnimDef::set_character(Character *character) {
    _character = character;
}

INLINE PT(Character) CActor::AnimDef::get_character() {
    return _character;
}

INLINE void CActor::AnimDef::set_name(const std::string &name) {
    _name = name;
}

INLINE std::string CActor::AnimDef::get_name() {
    return _name;
}

INLINE void CActor::AnimDef::set_index(int index) {
    _index = index;
}

INLINE int CActor::AnimDef::get_index() {
    return _index;
}

INLINE void CActor::AnimDef::set_play_rate(PN_stdfloat play_rate) {
    _play_rate = play_rate;
}

INLINE PN_stdfloat CActor::AnimDef::get_play_rate() {
    return _play_rate;
}

INLINE bool CActor::AnimDef::is_bound() {
    return _index >= 0;
}


/* Part Defitition */

INLINE CActor::PartDef::PartDef() {
}

INLINE CActor::PartDef::PartDef(const NodePath &char_np, PT(Character) character, const NodePath &part_model) {
    _character_np = char_np;
    _character = character;
    _part_model = part_model;
}

INLINE CActor::PartDef::PartDef(const CActor::PartDef &other) {
    _character_np = other._character_np;
    _character = other._character;
    _part_model = other._part_model;
    
    _anims_by_name.insert(other._anims_by_name.begin(), other._anims_by_name.end());
    _anims_by_index = other._anims_by_index;
    _weight_list.insert(other._weight_list.begin(), other._weight_list.end());
}

INLINE void CActor::PartDef::operator=(const CActor::PartDef &copy) {
    _character_np = copy._character_np;
    _character = copy._character;
    _part_model = copy._part_model;
    
    _anims_by_name.clear();
    _anims_by_index.clear();
    _weight_list.clear();
    
    _anims_by_name.insert(copy._anims_by_name.begin(), copy._anims_by_name.end());
    _anims_by_index = copy._anims_by_index;
    _weight_list.insert(copy._weight_list.begin(), copy._weight_list.end());
}