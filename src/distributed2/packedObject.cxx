/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file packedObject.cxx
 * @author brian
 * @date 2020-09-14
 */

#include "packedObject.h"
#include "dcClass.h"
#include "dcField.h"
#include "dcParameter.h"

TypeHandle PackedObject::_type_handle;

/**
 *
 */
PackedObject::
~PackedObject() {
#ifndef NDEBUG
  if (distributed2_cat.is_debug()) {
    distributed2_cat.debug()
      << "Destructing PackedObject " << this << ", _data: " << (void *)_data << "\n";
  }
#endif
  clear_data();
}

/**
 * Calculates which fields have different packed values between this
 * PackedObject and the specified data.
 *
 * NOTE: It is assumed that both buffers have the same length and specify
 *       the same fields in the same order.
 */
int PackedObject::
calc_delta(const char *data, size_t length, PackedObject::PackedFields &fields,
           vector_int &delta_fields) {
  if (fields.size() != _fields.size()) {
    return -1;
  }

  if (length == 0 || _length == 0) {
    return -1; // treat all fields as changed
  }

  int num_fields = get_num_fields();

  delta_fields.reserve(num_fields);

  for (int i = 0; i < num_fields; i++) {
    const PackedField &field = get_field(i);
    const PackedField &other_field = fields[i];

    if (field.length != other_field.length) {
      // If the packed field length is different, obviously the
      // value is different.
      delta_fields.push_back(i);

    } else if (memcmp(_data + field.offset, data + other_field.offset, field.length)) {
      // Actual bits are different
      delta_fields.push_back(i);
    }
  }

  return (int)delta_fields.size();
}

/**
 * Packs the absolute state onto a datagram suitable for sending over the
 * network.
 */
void PackedObject::
pack_datagram(Datagram &dg) {
  int num_fields = get_num_fields();
  dg.add_uint16(num_fields);

  for (int i = 0; i < num_fields; i++) {
    pack_field(dg, i);
  }
}

/**
 * Packs the indicated field onto the datagram.
 */
void PackedObject::
pack_field(Datagram &dg, int n) {
  const PackedField &field = get_field(n);
  dg.add_uint16(field.field_index);
  dg.append_data(_data + field.offset, field.length);
}
