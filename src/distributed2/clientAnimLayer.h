/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file clientAnimLayer.h
 * @author brian
 * @date 2021-05-24
 */

#ifndef CLIENTANIMLAYER_H
#define CLIENTANIMLAYER_H

#include "directbase.h"
#include "interpolatedVariable.h"
#include "animLayer.h"
#include "lerpFunctions.h"

/**
 * Contains data for an AnimLayer that is sent over the network and must be
 * interpolated by the client.
 */
class EXPCL_DIRECT_DISTRIBUTED2 ClientAnimLayer {
PUBLISHED:
  // This is the stuff that the client needs to interpolate for each layer.
  INLINE ClientAnimLayer(const AnimLayer &copy);

  INLINE bool operator == (const ClientAnimLayer &other) const;
  INLINE void operator *= (PN_stdfloat value);
  INLINE void operator += (const ClientAnimLayer &other);
  INLINE ClientAnimLayer operator / (PN_stdfloat value) const;
  INLINE ClientAnimLayer operator * (PN_stdfloat value) const;
  INLINE ClientAnimLayer operator - (const ClientAnimLayer &other) const;

  PN_stdfloat cycle;
  PN_stdfloat prev_cycle;
  PN_stdfloat weight;
  int order;
  int sequence;
  int sequence_parity;

public:
  ClientAnimLayer() = default;
};

// Specializations of the lerp functions used by InterpolatedVariable for the
// ClientAnimLayer.
INLINE ClientAnimLayer LoopingLerp(float percent, ClientAnimLayer &from, ClientAnimLayer &to);
INLINE ClientAnimLayer tlerp(float percent, ClientAnimLayer &from, ClientAnimLayer &to);
INLINE ClientAnimLayer LoopingLerp_Hermite(float percent, ClientAnimLayer &prev, ClientAnimLayer &from, ClientAnimLayer &to);
INLINE ClientAnimLayer Lerp_Hermite(float percent, ClientAnimLayer &prev, ClientAnimLayer &from, ClientAnimLayer &to);
INLINE void Lerp_Clamp(ClientAnimLayer &val);

BEGIN_PUBLISH
typedef InterpolatedVariable<ClientAnimLayer> InterpolatedClientAnimLayer;
EXPORT_TEMPLATE_CLASS(EXPCL_DIRECT_DISTRIBUTED2, EXPTP_DIRECT_DISTRIBUTED2, InterpolatedVariable<ClientAnimLayer>);
END_PUBLISH

#include "clientAnimLayer.I"

#endif // CLIENTANIMLAYER_H
