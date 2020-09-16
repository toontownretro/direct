/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file packedObject.h
 * @author lachbr
 * @date 2020-09-13
 */

#ifndef PACKEDOBJECT_H
#define PACKEDOBJECT_H

#include "config_distributed2.h"
#include "dcbase.h"
#include "pointerTo.h"
#include "changeFrameList.h"
#include "typedReferenceCount.h"
#include "deletedChain.h"
#include "datagram.h"

class DCClass;

/**
 * Represents the packed absolute state of a distributed object at a particular
 * point in time, stored as a block of memory.
 */
class EXPCL_DIRECT_DISTRIBUTED2 PackedObject : public TypedReferenceCount {
public:
  // Specifies where individual fields are in the buffer.
  struct PackedField {
    int field_index; // index into dclass _inherited_fields
    size_t offset; // where does the packed data for this field begin
    size_t length; // how big is the data for the field
  };

  typedef pvector<PackedField> PackedFields;

PUBLISHED:
  ALLOC_DELETED_CHAIN(PackedObject);

  INLINE PackedObject();
  INLINE ~PackedObject();

  INLINE void set_data(char *data, size_t length);
  INLINE void clear_data();
  INLINE const char *get_data() const;
  INLINE size_t get_length() const;

  INLINE void set_fields(PackedFields &&fields);
  INLINE void set_fields(const PackedFields &fields);
  INLINE const PackedField &get_field(int n) const;
  INLINE int get_num_fields() const;

  INLINE void set_snapshot_creation_tick(int tick);
  INLINE int get_snapshot_creation_tick() const;

  INLINE void set_class(DCClass *dclass);
  INLINE DCClass *get_class() const;

  INLINE void set_do_id(DOID_TYPE do_id);
  INLINE DOID_TYPE get_do_id() const;

  INLINE void set_change_frame_list(ChangeFrameList *list);
  INLINE ChangeFrameList *get_change_frame_list() const;
  INLINE PT(ChangeFrameList) take_change_frame_list();

  // If this PackedObject has a ChangeFrameList, then this calls through.
  // If not, it returns all fields.
  INLINE int get_fields_changed_after_tick(int tick, vector_int &out_fields);

  int calc_delta(const char *data, size_t length, PackedFields &fields,
                 vector_int &delta_fields);

  void pack_datagram(Datagram &dg);
  void pack_field(Datagram &dg, int n);

private:
  // Individual field information
  pvector<PackedField> _fields;

  char *_data;
  size_t _length;

  DCClass *_dclass;
  DOID_TYPE _do_id;

  PT(ChangeFrameList) _change_frame_list;

  // This is the tick the PackedObject was created on.
  int _creation_tick;
  bool _should_check_creation_tick;

public:
  static TypeHandle get_class_type() {
    return _type_handle;
  }
  static void init_type() {
    TypedReferenceCount::init_type();
    register_type(_type_handle, "PackedObject",
                  TypedReferenceCount::get_class_type());
    }
  virtual TypeHandle get_type() const {
    return get_class_type();
  }
  virtual TypeHandle force_init_type() {init_type(); return get_class_type();}

private:
  static TypeHandle _type_handle;
};

#include "packedObject.I"

#endif // PACKEDOBJECT_H
