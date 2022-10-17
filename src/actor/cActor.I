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
 * set_play_rate(float rate)
 * Set the play rate of given anim for a given part.
 * If no part is given, set for all parts in dictionary.
 * 
 * It used to be legal to let the animation name default to the
 * currently-playing anim, but this was confusing and could lead
 * to the wrong anim's play rate getting set.  Better to insist
 * on this parameter.
 * NOTE: sets play rate on all LODs
**/
INLINE void CActor::set_play_rate(PN_stdfloat rate) {
    set_play_rate(rate, EMPTY_STR, EMPTY_STR, 0);
}

/**
 * set_play_rate(float rate, string anim)
 * Set the play rate of given anim for a given part.
 * If no part is given, set for all parts in dictionary.
 * 
 * It used to be legal to let the animation name default to the
 * currently-playing anim, but this was confusing and could lead
 * to the wrong anim's play rate getting set.  Better to insist
 * on this parameter.
 * NOTE: sets play rate on all LODs
**/
INLINE void CActor::set_play_rate(PN_stdfloat rate, const std::string &anim) {
    set_play_rate(rate, anim, EMPTY_STR, 0);
}

/**
 * set_play_rate(float rate, string anim, string part_name)
 * Set the play rate of given anim for a given part.
 * If no part is given, set for all parts in dictionary.
 * 
 * It used to be legal to let the animation name default to the
 * currently-playing anim, but this was confusing and could lead
 * to the wrong anim's play rate getting set.  Better to insist
 * on this parameter.
 * NOTE: sets play rate on all LODs
**/
INLINE void CActor::set_play_rate(PN_stdfloat rate, const std::string &anim, const std::string &part_name) {
    set_play_rate(rate, anim, part_name, 0);
}

/**
 * get_play_rate()
 * 
 * Return the play rate of given anim for a given part.
 * If no part is given, assume first part in map.
 * If no anim is given, find the current anim for the part.
 * NOTE: Returns info only for an arbitrary LOD
**/
PN_stdfloat CActor::get_play_rate() {
    return get_play_rate(EMPTY_STR, EMPTY_STR, 0);
}

/**
 * get_play_rate(string anim_name)
 * 
 * Return the play rate of given anim for a given part.
 * If no part is given, assume first part in map.
 * If no anim is given, find the current anim for the part.
 * NOTE: Returns info only for an arbitrary LOD
**/
PN_stdfloat CActor::get_play_rate(const std::string &anim_name) {
    return get_play_rate(anim_name, EMPTY_STR, 0);
}

/**
 * get_play_rate(string anim_name, string part_name)
 * 
 * Return the play rate of given anim for a given part.
 * If no part is given, assume first part in map.
 * If no anim is given, find the current anim for the part.
 * NOTE: Returns info only for an arbitrary LOD
**/
PN_stdfloat CActor::get_play_rate(const std::string &anim_name, const std::string &part_name) {
    return get_play_rate(anim_name, part_name, 0);
}

int CActor::get_num_frames() {
    return get_num_frames(EMPTY_STR, EMPTY_STR, 0);
}

int CActor::get_num_frames(const std::string &anim_name) {
    return get_num_frames(anim_name, EMPTY_STR, 0);
}

int CActor::get_num_frames(const std::string &anim_name, const std::string &part_name) {
    return get_num_frames(anim_name, part_name, 0);
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
 * set_LOD_node()
 * Set the node that switches actor geometry in and out.
 * If one is not supplied as an argument, make one.
**/
INLINE void CActor::set_LOD_node() {
    LightReMutexHolder holder(_cactor_thread_lock);
    
    PT(LODNode) node = LODNode::make_default_lod("lod");
    NodePath nodepath(node);
    set_LOD_node(nodepath);
}

/**
 * Return the node that switches actor geometry in and out.
**/
INLINE LODNode *CActor::get_LOD_node() {
    if (_lod_node.is_empty() || !_lod_node.node()->is_of_type(LODNode::get_class_type())) { return nullptr; }
    
    return (LODNode *)_lod_node.node();
}

INLINE void CActor::use_LOD(int lod) {
    std::string lod_name = std::to_string(lod);
    
    use_LOD(lod_name);
}

INLINE void CActor::use_LOD(const std::string &lod_name) {
    LightReMutexHolder holder(_cactor_thread_lock);
        
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
 * Restore all switch distance info (usually after a use_LOD call)
**/
INLINE void CActor::reset_LOD() {
    LightReMutexHolder holder(_cactor_thread_lock);
    
    // Sanity check
    if (_lod_node.is_empty() || !_lod_node.node()->is_of_type(LODNode::get_class_type())) { return; }
    
    // Set our LOD nodes center.
    LODNode *lod_node = (LODNode *)_lod_node.node();
    lod_node->clear_force_switch();
}

/**
 * Return true if the actor has LODs, false otherwise.
**/
INLINE bool CActor::has_LOD() {
    return _has_LOD;
}

/**
 * add_LOD(int, int, int)
 * Add a named node under the LODNode to parent all geometry
 * of a specific LOD under.
**/
INLINE void CActor::add_LOD(int lod, int in_dist, int out_dist) {
    std::string lod_name = std::to_string(lod);
    
    add_LOD(lod_name, in_dist, out_dist);
}

/**
 * add_LOD(int, int, int, LPoint3f)
 * Add a named node under the LODNode to parent all geometry
 * of a specific LOD under.
**/
INLINE void CActor::add_LOD(int lod, int in_dist, int out_dist, const LPoint3f &center) {
    std::string lod_name = std::to_string(lod);
    
    add_LOD(lod_name, in_dist, out_dist, center);
}

/**
 * set_LOD(int, int, int)
 * Set the switch distance for given LOD
**/
INLINE void CActor::set_LOD(int lod, int in_dist, int out_dist) {
    std::string lod_name = std::to_string(lod);
    
    set_LOD(lod_name, in_dist, out_dist);
}

/**
 * get_LOD_index(int)
 * Safe method (but expensive) for retrieving the child index.
**/
INLINE int CActor::get_LOD_index(int lod) {
    std::string lod_name = std::to_string(lod);
    
    return get_LOD_index(lod_name);
}

/**
 * instance(NodePath path, string part_name, string joint_name)
 * Instance a NodePath to an actor part at a joint called joint_name
**/
INLINE NodePath CActor::instance(NodePath &path, const std::string &part_name, const std::string &joint_name) {
    return instance(path, part_name, joint_name, "lodRoot");
}

/**
 * attach(string part_name, string another_part_name, string joint_name)
 * Attach one actor part to another at a joint called joint_name
**/
INLINE void CActor::attach(const std::string &part_name, const std::string &another_part_name, const std::string &joint_name) {
    return attach(part_name, another_part_name, joint_name, "lodRoot");
}

/**
 * draw_in_front(string front_part_name, string back_part_name, int mode)
 * 
 * Arrange geometry so the front_part(s) are drawn in front of
 * back_part.
 * 
 * If mode == -1, the geometry is simply arranged to be drawn in
 * the correct order, assuming it is already under a
 * direct-render scene graph (like the DirectGui system).  That
 * is, front_part is reparented to back_part, and back_part is
 * reordered to appear first among its siblings.
 * 
 * If mode == -2, the geometry is arranged to be drawn in the
 * correct order, and depth test/write is turned off for
 * front_part.
 * 
 * If mode == -3, front_part is drawn as a decal onto back_part.
 * This assumes that front_part is mostly coplanar with and does
 * not extend beyond back_part, and that back_part is mostly flat
 * (not self-occluding).
 * 
 * If mode > 0, the front_part geometry is placed in the 'fixed'
 * bin, with the indicated drawing order.  This will cause it to
 * be drawn after almost all other geometry.  In this case, the
 * backPartName is actually unused.
 * 
 * Takes an optional argument root as the start of the search for the
 * given parts. Also takes optional lod name to refine search for the
 * named parts. If root and lod are defined, we search for the given
 * root under the given lod.
**/
INLINE void CActor::draw_in_front(const std::string &front_part_name, const std::string &back_part_name, int mode) {
    draw_in_front(front_part_name, back_part_name, mode, "", "");
}

/**
 * draw_in_front(string front_part_name, string back_part_name, int mode, string lod_name)
 * 
 * Arrange geometry so the front_part(s) are drawn in front of
 * back_part.
 * 
 * If mode == -1, the geometry is simply arranged to be drawn in
 * the correct order, assuming it is already under a
 * direct-render scene graph (like the DirectGui system).  That
 * is, front_part is reparented to back_part, and back_part is
 * reordered to appear first among its siblings.
 * 
 * If mode == -2, the geometry is arranged to be drawn in the
 * correct order, and depth test/write is turned off for
 * front_part.
 * 
 * If mode == -3, front_part is drawn as a decal onto back_part.
 * This assumes that front_part is mostly coplanar with and does
 * not extend beyond back_part, and that back_part is mostly flat
 * (not self-occluding).
 * 
 * If mode > 0, the front_part geometry is placed in the 'fixed'
 * bin, with the indicated drawing order.  This will cause it to
 * be drawn after almost all other geometry.  In this case, the
 * backPartName is actually unused.
 * 
 * Takes an optional argument root as the start of the search for the
 * given parts. Also takes optional lod name to refine search for the
 * named parts. If root and lod are defined, we search for the given
 * root under the given lod.
**/
INLINE void CActor::draw_in_front(const std::string &front_part_name, const std::string &back_part_name, int mode, const std::string &lod_name) {
    draw_in_front(front_part_name, back_part_name, mode, "", lod_name);
}

/**
 * get_part()
 * 
 * Find the named part in the optional named lod and return it, or
 * return a empty NodePath if not present.
**/
INLINE NodePath CActor::get_part() {
    return get_part("modelRoot", "lodRoot");
}

/**
 * get_part(string part_name)
 * 
 * Find the named part in the optional named lod and return it, or
 * return a empty NodePath if not present.
**/
NodePath CActor::get_part(const std::string &part_name) {
    return get_part(part_name, "lodRoot");
}

/**
 * get_part_model()
 * 
 * Returns a NodePath to the ModelRoot of the indicated part name.
**/
INLINE NodePath CActor::get_part_model() {
    return get_part_model("modelRoot", "lodRoot");
}

/**
 * get_part_model(string part_name)
 * 
 * Returns a NodePath to the ModelRoot of the indicated part name.
**/
NodePath CActor::get_part_model(const std::string &part_name) {
    return get_part_model(part_name, "lodRoot");
}


/**
 * get_part_bundle()
 * 
 * Find the named part in the optional named lod and return its
 * associated PartBundle, or return NULL if not present.
**/
INLINE PT(Character) CActor::get_part_bundle() {
    return get_part_bundle("modelRoot", "lodRoot");
}

/**
 * get_part_bundle(string part_name)
 * 
 * Find the named part in the optional named lod and return its
 * associated PartBundle, or return NULL if not present.
**/
INLINE PT(Character) CActor::get_part_bundle(const std::string &part_name) {
    return get_part_bundle(part_name, "lodRoot");
}

INLINE void CActor::face_away_from_viewer() {
    LightReMutexHolder holder(_cactor_thread_lock);
    
    NodePath &geom_node = get_geom_node();
    geom_node.set_h(180);
}

INLINE void CActor::face_towards_viewer() {
    LightReMutexHolder holder(_cactor_thread_lock);
    
    NodePath &geom_node = get_geom_node();
    geom_node.set_h(0);
}

INLINE const CActor::PartBundleDict &CActor::get_part_bundle_dict() const {
    return _part_bundle_dict;
}

INLINE void CActor::list_joints() {
    list_joints("", "");
}

INLINE const Filename CActor::get_anim_filename(const std::string &anim_name) {
    return get_anim_filename(anim_name, "");
}

INLINE NodePath *CActor::control_joint(NodePath *node, const std::string &part_name, const std::string &joint_name) {
    return control_joint(node, part_name, joint_name, std::string("lodRoot"));
}


/* Animation Defitition */

INLINE CActor::AnimDef::AnimDef(Filename filename) : _name("default"), _filename(filename) {

}

INLINE CActor::AnimDef::AnimDef(Filename filename, PT(AnimChannel) channel) : _name("default"), _filename(filename) {
    set_animation_channel(channel);
}

INLINE CActor::AnimDef::AnimDef(Filename filename, PT(AnimChannel) channel, PT(Character) character) : _name("default"), _filename(filename) {
    set_animation_channel(channel);
    set_character(character);
}

INLINE CActor::AnimDef::AnimDef(const CActor::AnimDef &other)  {
    if (other._channel != nullptr) { set_animation_channel(other.get_animation_channel()); }
    if (other._character != nullptr) { set_character(other.get_character()); }
    set_index(other.get_index());
    set_play_rate(other.get_play_rate());
    set_name(other.get_name());
    set_filename(other.get_filename());
}

INLINE CActor::AnimDef::AnimDef(CActor::AnimDef &&other) noexcept {
    // Since this is a move constructor, We reference the members directly.
    
    _channel = std::exchange(other._channel, nullptr);
    _character = std::exchange(other._character, nullptr);
    _index = std::exchange(other._index, -1);
    _play_rate = std::exchange(other._play_rate, 1.0);
    _name = std::move(other._name);
    _filename = std::move(other._filename);
}

INLINE void CActor::AnimDef::operator=(const CActor::AnimDef &copy) {
    if (copy._channel != nullptr) { set_animation_channel(copy.get_animation_channel()); }
    if (copy._character != nullptr) { set_character(copy.get_character()); }
    set_index(copy.get_index());
    set_play_rate(copy.get_play_rate());
    set_name(copy.get_name());
    set_filename(copy.get_filename());
}

INLINE CActor::AnimDef &CActor::AnimDef::operator=(CActor::AnimDef &&other) noexcept {
    // If we're assigning to ourself. Do nothing.
    if (this == &other) { return *this; }
    
    // Since this is a move assignment operation, We reference the members directly.
    
    _channel = std::exchange(other._channel, nullptr);
    _character = std::exchange(other._character, nullptr);
    _index = std::exchange(other._index, -1);
    _play_rate = std::exchange(other._play_rate, 1.0);
    _name = std::move(other._name);
    _filename = std::move(other._filename);
    return *this;
}

INLINE void CActor::AnimDef::set_name(const std::string &name) {
    LightReMutexHolder holder(_cactor_animdef_thread_lock);
    
    _name = std::string(name);
}

INLINE const std::string &CActor::AnimDef::get_name() const {
    return _name;
}

INLINE void CActor::AnimDef::set_filename(const std::string &filename) {
    LightReMutexHolder holder(_cactor_animdef_thread_lock);
    
    _filename = Filename(filename);
}

INLINE void CActor::AnimDef::set_filename(const Filename &filename) {
    LightReMutexHolder holder(_cactor_animdef_thread_lock);
    
    _filename = Filename(filename);
}

INLINE const Filename &CActor::AnimDef::get_filename() const {
    return _filename;
}

INLINE void CActor::AnimDef::set_animation_channel(AnimChannel *channel) {
    LightReMutexHolder holder(_cactor_animdef_thread_lock);
    
    _channel = channel;
}

INLINE void CActor::AnimDef::set_animation_channel(PT(AnimChannel) channel) {
    LightReMutexHolder holder(_cactor_animdef_thread_lock);
    
    _channel = channel.p();
}

INLINE AnimChannel *CActor::AnimDef::get_animation_channel() const {
    return _channel;
}

INLINE bool CActor::AnimDef::has_animation_channel() const {
    return _channel != nullptr;
}

INLINE void CActor::AnimDef::set_character(Character *character) {
    LightReMutexHolder holder(_cactor_animdef_thread_lock);
    
    _character = character;
}

INLINE void CActor::AnimDef::set_character(PT(Character) character) {
    LightReMutexHolder holder(_cactor_animdef_thread_lock);
    
    _character = character.p();
}

INLINE Character *CActor::AnimDef::get_character() const {
    return _character;
}

INLINE void CActor::AnimDef::set_index(int index) {
    LightReMutexHolder holder(_cactor_animdef_thread_lock);
    
    _index = index;
}

INLINE int CActor::AnimDef::get_index() const {
    return _index;
}

INLINE void CActor::AnimDef::set_play_rate(PN_stdfloat play_rate) {
    LightReMutexHolder holder(_cactor_animdef_thread_lock);
    
    _play_rate = play_rate;
}

INLINE PN_stdfloat CActor::AnimDef::get_play_rate() const {
    return _play_rate;
}

INLINE bool CActor::AnimDef::is_bound() const {
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
    _anims_by_index.assign(other._anims_by_index.begin(), other._anims_by_index.end());
    _weight_list.insert(other._weight_list.begin(), other._weight_list.end());
}

INLINE void CActor::PartDef::operator=(const CActor::PartDef &copy) {
    _character_np = copy._character_np;
    _character = copy._character;
    _part_model = copy._part_model;
    
    // Free all of our vectors contents, and shrink them back down.
    _anims_by_name.clear();
    _anims_by_index.clear();
    _anims_by_index.shrink_to_fit();
    _weight_list.clear();
    
    // Copy over the other vectors.
    _anims_by_name.insert(copy._anims_by_name.begin(), copy._anims_by_name.end());
    _anims_by_index.assign(copy._anims_by_index.begin(), copy._anims_by_index.end());
    _weight_list.insert(copy._weight_list.begin(), copy._weight_list.end());
}

INLINE PT(Character) CActor::PartDef::get_character() const {
    return _character;
}

INLINE const NodePath &CActor::PartDef::get_character_nodepath() const {
    return _character_np;
}