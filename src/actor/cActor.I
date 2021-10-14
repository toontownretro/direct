INLINE void CActor::set_geom_node(NodePath &node) {
    _geom_node = node;
}

INLINE NodePath &CActor::get_geom_node() {
    return _geom_node;
}


INLINE CActor::AnimDef::AnimDef(Filename filename, PT_AnimChannelTable channel, Character *character) : _filename(filename) {
    _channel = channel;
    _character = character;
}

INLINE void CActor::AnimDef::set_filename(std::string &filename) {
    _filename = Filename(filename);
}

INLINE void CActor::AnimDef::set_filename(Filename &filename) {
    _filename = filename;
}

INLINE Filename &CActor::AnimDef::get_filename() {
    return _filename;
}

INLINE void CActor::AnimDef::set_animation_table(PT_AnimChannelTable channel) {
    _channel = channel;
}

INLINE PT_AnimChannelTable CActor::AnimDef::get_animation_table() {
    return _channel;
}

INLINE void CActor::AnimDef::set_character(Character *character) {
    _character = character;
}

INLINE PT(Character) CActor::AnimDef::get_character() {
    return _character;
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

INLINE CActor::PartDef::PartDef(NodePath *char_np, Character *character, NodePath *part_model) {
    _character_np = char_np;
    _character = character;
    _part_model = part_model;
}