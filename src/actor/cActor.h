#pragma once

#include "animChannel.h"
#include "animChannelBundle.h"
#include "animChannelTable.h"
#include "character.h"
#include "characterNode.h"
#include "directbase.h"
#include "filename.h"
#include "loader.h"
#include "loaderOptions.h"
#include "lodNode.h"
#include "luse.h"
#include "nodePath.h"
#include "nodePathCollection.h"
#include "modelRoot.h"
#include "modelNode.h"
#include "pandaNode.h"
#include "pmap.h"
#include "pointerTo.h"
#include "pvector.h"
#include "weightList.h"

#include "pt_AnimChannelTable.h"
#include "pt_Character.h"

#include <algorithm>
#include <functional>
#include <tuple>
#include <utility>

struct MultipartLODActorData {
    std::string lod_name;
    std::string part_name;
    NodePath model_node;
};

struct MultipartLODActorDataWPath {
    std::string lod_name;
    std::string part_name;
    std::string model_path;
};

// Forward declarations.
class CActor;

class EXPCL_DIRECT_ACTOR CActor : NodePath {
    class EXPCL_DIRECT_ACTOR AnimDef {
        public:
            INLINE AnimDef(Filename filename = Filename(), PT(AnimChannel) channel = nullptr, PT(Character) character = nullptr);
            INLINE ~AnimDef() = default;
            
            INLINE void set_filename(const std::string &filename);
            INLINE void set_filename(const Filename &filename);
            INLINE const Filename &get_filename();
            
            INLINE void set_animation_channel(AnimChannel *channel);
            INLINE PT(AnimChannel) get_animation_channel();
            
            INLINE void set_character(Character *character);
            INLINE PT(Character) get_character();
            
            INLINE void set_name(const std::string &name);
            INLINE std::string get_name();
            
            INLINE void set_index(int index);
            INLINE int get_index();
            
            INLINE void set_play_rate(PN_stdfloat play_rate);
            INLINE PN_stdfloat get_play_rate();
            
            INLINE bool is_bound();
            
        private:
            Filename _filename;
            
            PT(AnimChannel) _channel;
            PT(Character) _character;
            
            std::string _name = "";
            
            int _index = -1;
            PN_stdfloat _play_rate = 1.0;
    };
    
    class EXPCL_DIRECT_ACTOR PartDef {
        friend class CActor;
        
        public:
            INLINE PartDef();
            INLINE PartDef(const NodePath &char_np, PT(Character) character, const NodePath &part_model);
            INLINE PartDef(const PartDef &other);
            INLINE ~PartDef() = default;
            
            INLINE void PartDef::operator=(const PartDef &copy);
            
            int get_channel_index(const std::string &anim_name);

            AnimDef *get_anim_def(int index);
            AnimDef *get_anim_def(const std::string &anim_name);
            
        protected:
            NodePath _character_np = NodePath();
            PT(Character) _character = nullptr;
            NodePath _part_model = NodePath();
            
            pmap<std::string, AnimDef> _anims_by_name;
            pvector<AnimDef> _anims_by_index;
            pmap<std::string, WeightList> _weight_list;
    };
    
    PUBLISHED:
        CActor(bool flattenable=true, bool set_final=false);
        CActor(const CActor &other);
        ~CActor();
        
        void CActor::operator=(const CActor &copy);
        
        void load_model(const NodePath &model_node, const std::string &part_name, const std::string &lod_name, bool copy=true, bool ok_missing=false, bool keep_model=false);
        void load_model(const std::string &model_path, const std::string &part_name, const std::string &lod_name, bool copy=true, bool ok_missing=false, bool keep_model=false);
        
        INLINE void set_geom_node(const NodePath &node);
        INLINE const NodePath &get_geom_node() const;
        
        INLINE void set_lod_node();
        void set_lod_node(const NodePath &node);
        
        INLINE LODNode *get_lod_node();
        
        INLINE void use_lod(const std::string &lod_name);
        INLINE void reset_lod();
        INLINE bool has_lod();
        
        void add_lod(const std::string &lod_name, int in_dist=0, int out_dist=0);
        void add_lod(const std::string &lod_name, int in_dist, int out_dist, const LPoint3f &center);
        
        void set_lod(const std::string &lod_name, int in_dist=0, int out_dist=0);
        
        int get_lod_index(const std::string &lod_name);
        
        NodePath get_lod(const std::string &lod_name);
        
        void set_center(const LPoint3f center = LPoint3f(0.0, 0.0, 0.0));
        
    public:
        //////////////////////////////
        // Initializers w/o Animations
        //////////////////////////////
        
        // Single-part Actor w/o LOD
        CActor(const std::string &model_path, bool copy=true, bool flattenable=true, bool set_final=false, bool ok_missing=false);
        CActor(const NodePath &model_node, bool copy=true, bool flattenable=true, bool set_final=false, bool ok_missing=false);
        
        // Multi-part Actor w/o LOD
        CActor(const pmap<std::string, std::string> &models, bool copy=true, bool flattenable=true, bool set_final=false, bool ok_missing=false);
        CActor(const pmap<std::string, NodePath> &models, bool copy=true, bool flattenable=true, bool set_final=false, bool ok_missing=false);
        
        // Single-part Actor w/ LOD
        CActor(const pmap<std::string, std::string> &models, NodePath &lod_node, bool copy=true, bool flattenable=true, bool set_final=false, bool ok_missing=false);
        CActor(const pmap<std::string, NodePath> &models, NodePath &lod_node, bool copy=true, bool flattenable=true, bool set_final=false, bool ok_missing=false);
        
        // Multi-part Actor w/ LOD
        CActor(const pvector<MultipartLODActorDataWPath> &models, NodePath &lod_node, bool copy=true, bool flattenable=true, bool set_final=false, bool ok_missing=false);
        CActor(const pvector<MultipartLODActorData> &models, NodePath &lod_node, bool copy=true, bool flattenable=true, bool set_final=false, bool ok_missing=false);
        
        //////////////////////////////
        // Initializers w/ Animations
        //////////////////////////////
        
        // Single-part Actor w/o LOD
        CActor(const std::string &model_path, const pvector<std::pair<std::string, std::string> > &anims, bool copy=true, bool flattenable=true, bool set_final=false, bool ok_missing=false);
        CActor(const NodePath &model_node, const pvector<std::pair<std::string, std::string> > &anims, bool copy=true, bool flattenable=true, bool set_final=false, bool ok_missing=false);
        
        // Multi-part Actor w/o LOD
        CActor(const pmap<std::string, std::string> &models, const pmap<std::string, pvector<std::pair<std::string, std::string> > > &anims, bool copy=true, bool flattenable=true, bool set_final=false, bool ok_missing=false);
        CActor(const pmap<std::string, NodePath> &models, const pmap<std::string, pvector<std::pair<std::string, std::string> > > &anims, bool copy=true, bool flattenable=true, bool set_final=false, bool ok_missing=false);
        
        // Single-part Actor w/ LOD
        CActor(const pmap<std::string, std::string> &models, NodePath &lod_node, const pvector<std::pair<std::string, std::string> > &anims, bool copy=true, bool flattenable=true, bool set_final=false, bool ok_missing=false);
        CActor(const pmap<std::string, NodePath> &models, NodePath &lod_node, const pvector<std::pair<std::string, std::string> > &anims, bool copy=true, bool flattenable=true, bool set_final=false, bool ok_missing=false);
        
        // Multi-part Actor w/ LOD
        CActor(const pvector<MultipartLODActorDataWPath> &models, NodePath &lod_node, const pmap<std::string, pvector<std::pair<std::string, std::string> > > &anims, 
               bool copy=true, bool flattenable=true, bool set_final=false, bool ok_missing=false);
        CActor(const pvector<MultipartLODActorData> &models, NodePath &lod_node, const pmap<std::string, pvector<std::pair<std::string, std::string> > > &anims, 
               bool copy=true, bool flattenable=true, bool set_final=false, bool ok_missing=false);
        
        void load_anims(const pvector<std::pair<std::string, std::string> > &anims, const std::string &part_name, const std::string &lod_name, bool load_now=false);
        
    private:
        void initialize_geom_node(bool flattenable=true);
        
        void copy_part_bundles(const CActor &other);
        
        AnimChannel *load_anim(const std::string &filename);
        AnimChannel *load_anim(const Filename &filename);
        
        bool bind_anim(PartDef &part_def, AnimDef &anim_def, PT(AnimChannel) channel);
        bool load_and_bind_anim(PartDef &part_def, AnimDef &anim_def);
        
        void load_model_internal(NodePath &model, const std::string &part_name, const std::string &lod_name, bool copy, bool ok_missing, bool keep_model);
        
        void prepare_bundle(const NodePath &bundle_np, const NodePath &part_model, const std::string &part_name, const std::string &lod_name);
        
        
        bool _got_name = false;
        bool _has_LOD = false;
        
        PT(Loader) loader = Loader::get_global_ptr();
        
        LoaderOptions model_loader_options = LoaderOptions(LoaderOptions::LF_search | LoaderOptions::LF_report_errors | LoaderOptions::LF_convert_skeleton);
        LoaderOptions anim_loader_options = LoaderOptions(LoaderOptions::LF_search | LoaderOptions::LF_report_errors | LoaderOptions::LF_convert_anim);
        
        LPoint3f _lod_center = LPoint3f(0.0, 0.0, 0.0);
        
        NodePath _geom_node = NodePath();
        NodePath _lod_node = NodePath();
        
        std::string part_prefix = "__Actor_";
        
        pmap<std::string, PartDef> _part_bundle_dict;
        pmap<std::string, std::pair<int, int>> _switches;
        
        pvector<std::string> _sorted_LOD_names;
};


#include "cActor.I"