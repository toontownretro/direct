#pragma once

#include "directbase.h"
#include "pointerTo.h"
#include "animChannelTable.h"
#include "character.h"
#include "characterNode.h"
#include "filename.h"
#include "pmap.h"
#include "pvector.h"
#include "pandaNode.h"
#include "nodePath.h"
#include "modelRoot.h"
#include "modelNode.h"
#include "loader.h"

#include "pt_AnimChannelTable.h"
#include "pt_Character.h"


class EXPCL_DIRECT_ACTOR CActor : NodePath {
    class EXPCL_DIRECT_ACTOR AnimDef {
        public:
            INLINE AnimDef(Filename filename = Filename(), PT_AnimChannelTable channel = nullptr, Character *character = nullptr);
            INLINE ~AnimDef() = default;
            
            INLINE void set_filename(std::string &filename);
            INLINE void set_filename(Filename &filename);
            INLINE Filename &get_filename();
            
            INLINE void set_animation_table(PT_AnimChannelTable channel);
            INLINE PT_AnimChannelTable get_animation_table();
            
            INLINE void set_character(Character *character);
            INLINE PT(Character) get_character();
            
            INLINE void set_index(int index);
            INLINE int get_index();
            
            INLINE void set_play_rate(PN_stdfloat play_rate);
            INLINE PN_stdfloat get_play_rate();
            
            INLINE bool is_bound();
            
        private:
            Filename _filename;
            PT_AnimChannelTable _channel;
            PT(Character) _character;
            
            int _index = -1;
            PN_stdfloat _play_rate = 1.0;
    };
    
    class EXPCL_DIRECT_ACTOR PartDef {
        friend class CActor;
        
        public:
            INLINE PartDef(NodePath *char_np, Character *character, NodePath *part_model);
            INLINE ~PartDef() = default;
            
            int get_channel_index(std::string &anim_name);

            AnimDef *get_anim_def(int index);
            AnimDef *get_anim_def(std::string &anim_name);
            
        protected:
            NodePath *_character_np;
            PT(Character) _character;
            NodePath *_part_model;
            
            pmap<std::string, AnimDef> _anims_by_name;
            pvector<AnimDef> _anims_by_index;
            pmap<std::string, int> _weight_list;
    };
    
    PUBLISHED:
        CActor();
        CActor(std::string &modelName, bool copy=true, bool flattenable=true, bool set_final=false, bool ok_missing=false);
        CActor(const CActor &other);
        ~CActor();
        
        CActor &operator=(class CActor const &) = default;
        
        INLINE void set_geom_node(NodePath &node);
        INLINE NodePath &get_geom_node();
        
        void load_model(NodePath &model_path, std::string &part_name, std::string &lod_name, bool copy=true, bool ok_missing=false, bool auto_bind_anims=true, bool keep_model=false);
        
    private:
        bool _has_LOD = false;
        
        NodePath _geom_node;
        NodePath _lod_node;
        
        std::string part_prefix = "__Actor_";
        
        pmap<std::string, PartDef> _part_bundle_dict;
        pvector<std::string> _sorted_LOD_names;
        
        PT(Loader) loader = Loader::get_global_ptr();
};


#include "cActor.I"