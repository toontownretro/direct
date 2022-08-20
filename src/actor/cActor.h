#pragma once

#include "animChannel.h"
#include "animChannelBundle.h"
#include "animChannelTable.h"
#include "animLayer.h"
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
        PUBLISHED:
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
        
        PUBLISHED:
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
        virtual ~CActor();
        
        void CActor::operator=(const CActor &copy);
        
        void load_model(const NodePath &model_node, const std::string &part_name, const std::string &lod_name, bool copy=true, bool ok_missing=false, bool keep_model=false);
        void load_model(const std::string &model_path, const std::string &part_name, const std::string &lod_name, bool copy=true, bool ok_missing=false, bool keep_model=false);
        
        void stop(int layer=1, bool kill=false);
        void stop(const std::string &anim_name, const std::string &part_name, int layer=1, bool kill=false);
        
        void play(const std::string &anim_name, int from_frame=0, int to_frame=-1, int layer=0, PN_stdfloat play_rate=1.0, bool auto_kill=false, PN_stdfloat blend_in=0.0, PN_stdfloat blend_out=0.0);
        void play(int channel, int from_frame=0, int to_frame=-1, int layer=0, PN_stdfloat play_rate=1.0, bool auto_kill=false, PN_stdfloat blend_in=0.0, PN_stdfloat blend_out=0.0);
        void play(const std::string &anim_name, const std::string &part_name, int from_frame=0, int to_frame=-1, int layer=0, PN_stdfloat play_rate=1.0, bool auto_kill=false, PN_stdfloat blend_in=0.0, PN_stdfloat blend_out=0.0);
        void play(int channel, const std::string &part_name, int from_frame=0, int to_frame=-1, int layer=0, PN_stdfloat play_rate=1.0, bool auto_kill=false, PN_stdfloat blend_in=0.0, PN_stdfloat blend_out=0.0);
        
        void loop(const std::string &anim_name, bool restart=true, int from_frame=0, int to_frame=-1, int layer=0, PN_stdfloat play_rate=1.0, PN_stdfloat blend_in=0.0);
        void loop(int channel, bool restart=true, int from_frame=0, int to_frame=-1, int layer=0, PN_stdfloat play_rate=1.0, PN_stdfloat blend_in=0.0);
        void loop(const std::string &anim_name, const std::string &part_name, bool restart=true, int from_frame=0, int to_frame=-1, int layer=0, PN_stdfloat play_rate=1.0, PN_stdfloat blend_in=0.0);
        void loop(int channel, const std::string &part_name, bool restart=true, int from_frame=0, int to_frame=-1, int layer=0, PN_stdfloat play_rate=1.0, PN_stdfloat blend_in=0.0);
        
        void pingpong(const std::string &anim_name, bool restart=true, int from_frame=0, int to_frame=-1, int layer=0, PN_stdfloat play_rate=1.0, PN_stdfloat blend_in=0.0);
        void pingpong(int channel, bool restart=true, int from_frame=0, int to_frame=-1, int layer=0, PN_stdfloat play_rate=1.0, PN_stdfloat blend_in=0.0);
        void pingpong(const std::string &anim_name, const std::string &part_name, bool restart=true, int from_frame=0, int to_frame=-1, int layer=0, PN_stdfloat play_rate=1.0, PN_stdfloat blend_in=0.0);
        void pingpong(int channel, const std::string &part_name, bool restart=true, int from_frame=0, int to_frame=-1, int layer=0, PN_stdfloat play_rate=1.0, PN_stdfloat blend_in=0.0);
        
        void pose(const std::string &anim_name, const std::string &part_name, const std::string &lod_name, int frame=0, int layer=0, PN_stdfloat blend_in=0.0, PN_stdfloat blend_out=0.0);
        void pose(int channel, const std::string &part_name, const std::string &lod_name, int frame=0, int layer=0, PN_stdfloat blend_in=0.0, PN_stdfloat blend_out=0.0);
        
        void set_transition(const std::string &anim_name, const std::string &part_name, const std::string &lod_name, bool flag=false);
        void set_transition(int channel, const std::string &part_name, const std::string &lod_name, bool flag=false);
        
        INLINE void set_geom_node(const NodePath &node);
        INLINE NodePath &get_geom_node();
        
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
        
        std::string get_current_anim(int layer=0);
        std::string get_current_anim(const std::string &part_name, int layer=0);
        
        int get_current_channel(int layer=0);
        int get_current_channel(const std::string &part_name, int layer=0);
        
        PN_stdfloat get_channel_length(int channel=0);
        PN_stdfloat get_channel_length(const std::string &part_name, int channel=0);
        
        int get_channel_activity(int channel=0, int index=0);
        int get_channel_activity(const std::string &part_name, int channel=0, int index=0);
        
        int get_channel_for_activity(int activity=0, int seed=0, int layer=0);
        int get_channel_for_activity(const std::string &part_name, int activity=0, int seed=0, int layer=0);
        
        int get_current_activity(int layer=0);
        int get_current_activity(const std::string &part_name, int layer=0);
        
        bool is_current_channel_finished(int layer=0);
        bool is_current_channel_finished(const std::string &part_name, int layer=0);
        
        bool is_channel_playing(int layer=0);
        bool is_channel_playing(const std::string &part_name, int layer=0);
        
        PN_stdfloat get_cycle(int layer=0);
        PN_stdfloat get_cycle(const std::string &part_name, int layer=0);
        
        int get_current_frame(int layer=0);
        int get_current_frame(const std::string &part_name, int layer=0);
        int get_current_frame(const std::string &anim_name, const std::string &part_name, int layer=0);
        
        // These functions compensate for actors that are modeled facing the viewer,
        // but need to face away from the camera in the game.
        INLINE void face_away_from_viewer();
        INLINE void face_towards_viewer();
        
        void advance();
        void advance(const std::string &part_name);
        
        void set_auto_advance(bool flag=true);
        void set_auto_advance(const std::string &part_name, bool flag=true);
        
        void set_blend(bool frame_blend=false, bool transition_blend=true);
        void set_blend(const std::string &part_name, bool frame_blend=false, bool transition_blend=true);
        
        INLINE void list_joints();
        void list_joints(const std::string &part_name, const std::string &lod_name);
        
        INLINE const Filename get_anim_filename(const std::string &anim_name);
        const Filename get_anim_filename(const std::string &anim_name, const std::string &part_name);
        
        virtual void post_flatten();
        
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
        
        pvector<AnimDef> get_anim_defs(const std::string &anim_name);
        pvector<AnimDef> get_anim_defs(int anim_index);
        pvector<AnimDef> get_anim_defs(const std::string &anim_name, const std::string &part_name, const std::string &lod_name);
        pvector<AnimDef> get_anim_defs(int anim_index, const std::string &part_name, const std::string &lod_name);
        pvector<AnimDef> get_anim_defs(const std::string &anim_name, const pvector<std::string> &part_names, const std::string &lod_name);
        pvector<AnimDef> get_anim_defs(int anim_index, const pvector<std::string> &part_names, const std::string &lod_name);
        
        pvector<PartDef> get_part_defs();
        pvector<PartDef> get_part_defs(const std::string &part_name, const std::string &lod_name);
        pvector<PartDef> get_part_defs(const pvector<std::string> &part_names, const std::string &lod_name);
        
        pvector<PT(Character)> get_part_bundles();
        pvector<PT(Character)> get_part_bundles(const std::string &part_name);
        
    private:
        void initialize_geom_node(bool flattenable=true);
        
        INLINE const NodePath &get_geom_node() const;
        
        INLINE const pmap<std::string, PartDef> &get_part_bundle_dict() const;
        
        void do_list_joints(std::stringstream &ss, PT(Character) character, int indent_level, int joint);
        
        void copy_part_bundles(const CActor &other);
        
        INLINE AnimChannel *load_anim(const std::string &filename);
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