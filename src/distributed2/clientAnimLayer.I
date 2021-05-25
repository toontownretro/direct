/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file clientAnimLayer.I
 * @author brian
 * @date 2021-05-24
 */

/**
 * Initializes a ClientAnimLayer from an AnimLayer.
 */
INLINE ClientAnimLayer::
ClientAnimLayer(const AnimLayer &copy) :
  cycle(copy._cycle),
  prev_cycle(copy._prev_cycle),
  weight(copy._weight),
  order(copy._order),
  sequence(copy._sequence),
  sequence_parity(copy._sequence_parity)
{
}

/**
 *
 */
INLINE bool ClientAnimLayer::
operator == (const ClientAnimLayer &other) const {
  return cycle == other.cycle &&
         prev_cycle == other.prev_cycle &&
         weight == other.weight &&
         order == other.order &&
         sequence == other.sequence &&
         sequence_parity == other.sequence_parity;
}

/**
 *
 */
INLINE void ClientAnimLayer::
operator *= (PN_stdfloat value) {
  cycle *= value;
  weight *= value;
}

/**
 *
 */
INLINE void ClientAnimLayer::
operator += (const ClientAnimLayer &other) {
  cycle += other.cycle;
  weight += other.weight;
}


/**
 *
 */
INLINE ClientAnimLayer ClientAnimLayer::
operator / (const PN_stdfloat value) const {
  ClientAnimLayer result;
  result.cycle = cycle / value;
  result.weight = weight / value;
  result.order = order;
  result.prev_cycle = prev_cycle;
  result.sequence = sequence;
  result.sequence_parity = sequence_parity;
  return result;
}

/**
 *
 */
INLINE ClientAnimLayer ClientAnimLayer::
operator * (PN_stdfloat value) const {
  ClientAnimLayer result;
  result.cycle = cycle * value;
  result.weight = weight * value;
  result.order = order;
  result.prev_cycle = prev_cycle;
  result.sequence = sequence;
  result.sequence_parity = sequence_parity;
  return result;
}

/**
 *
 */
INLINE ClientAnimLayer ClientAnimLayer::
operator - (const ClientAnimLayer &other) const {
  ClientAnimLayer result;
  result.cycle = cycle - other.cycle;
  result.weight = weight - other.weight;
  result.order = other.order;
  result.prev_cycle = other.prev_cycle;
  result.sequence = other.sequence;
  result.sequence_parity = sequence_parity;
  return result;
}

/**
 *
 */
INLINE ClientAnimLayer
LoopingLerp(float percent, ClientAnimLayer &from, ClientAnimLayer &to) {
  ClientAnimLayer output;
  output.sequence = to.sequence;
  output.cycle = LoopingLerp(percent, (float)from.cycle, (float)to.cycle);
  output.prev_cycle = to.prev_cycle;
  output.weight = tlerp(percent, (float)from.weight, (float)to.weight);
  output.order = to.order;
  output.sequence_parity = to.sequence_parity;
  return output;
}

/**
 *
 */
INLINE ClientAnimLayer
tlerp(float percent, ClientAnimLayer &from, ClientAnimLayer &to) {
  ClientAnimLayer output;
  output.sequence = to.sequence;
  output.cycle = tlerp(percent, (float)from.cycle, (float)to.cycle);
  output.prev_cycle = to.prev_cycle;
  output.weight = tlerp(percent, from.weight, to.weight);
  output.order = to.order;
  output.sequence_parity = to.sequence_parity;
  return output;
}

/**
 *
 */
INLINE ClientAnimLayer
LoopingLerp_Hermite(float percent, ClientAnimLayer &prev, ClientAnimLayer &from, ClientAnimLayer &to) {
  ClientAnimLayer output;
  output.sequence = to.sequence;
  output.cycle = LoopingLerp_Hermite(percent, (float)prev.cycle, (float)from.cycle, (float)to.cycle);
  output.prev_cycle = to.prev_cycle;
  output.weight = tlerp(percent, from.weight, to.weight);
  output.order = to.order;
  output.sequence_parity = to.sequence_parity;
  return output;
}

/**
 *
 */
INLINE ClientAnimLayer
Lerp_Hermite(float percent, ClientAnimLayer &prev, ClientAnimLayer &from, ClientAnimLayer &to) {
  ClientAnimLayer output;
  output.sequence = to.sequence;
  output.cycle = Lerp_Hermite(percent, (float)prev.cycle, (float)from.cycle, (float)to.cycle);
  output.prev_cycle = to.prev_cycle;
  output.weight = tlerp(percent, from.weight, to.weight);
  output.order = to.order;
  output.sequence_parity = to.sequence_parity;
  return output;
}

/**
 *
 */
INLINE void
Lerp_Clamp(ClientAnimLayer &val) {
}
