/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file interpolatedVariable.h
 * @author brian
 * @date 2021-05-03
 */

#ifndef INTERPOLATEDVARIABLE_H
#define INTERPOLATEDVARIABLE_H

#include "directbase.h"
#include "config_distributed2.h"
#include "referenceCount.h"
#include "luse.h"
#include "circBuffer.h"
#include "clockObject.h"
#include "pdeque.h"
#include "lerpFunctions.h"
#include "mathutil_misc.h"

static constexpr double extra_interpolation_history_stored = 0.05;

template <class Type>
class EXPCL_DIRECT_DISTRIBUTED2 SamplePointBase {
public:
  INLINE SamplePointBase() { timestamp = 0.0; }
  Type value;
  double timestamp;

  INLINE SamplePointBase(const SamplePointBase<Type> &other) {
    value = other.value;
    timestamp = other.timestamp;
  }

  INLINE void operator = (const SamplePointBase<Type> &other) {
    value = other.value;
    timestamp = other.timestamp;
  }
};

class EXPCL_DIRECT_DISTRIBUTED2 InterpolationContext {
PUBLISHED:
  INLINE InterpolationContext();
  INLINE ~InterpolationContext();

  INLINE static void enable_extrapolation(bool flag);
  INLINE static bool has_context();
  INLINE static bool is_extrapolation_allowed();
  INLINE static void set_last_timestamp(double time);
  INLINE static double get_last_timestamp();

private:
  InterpolationContext *_next;
  bool _old_allow_extrapolation;
  double _old_last_timestamp;

  static InterpolationContext *_head;
  static bool _allow_extrapolation;
  static double _last_timestamp;
};

/**
 * A variable whose changes in values are buffered and interpolated.  The type
 * used needs to have vector-like math operators (/, *, etc).
 *
 * The user should record changes in values to the variable and associate it
 * with a timestamp.  Later, an interpolated value can be calculated based
 * on the current rendering time, which can be retrieved by the user.
 *
 * Implementation derived from InterpolatedVar code in Valve's Source Engine.
 */
template <class Type>
class EXPCL_DIRECT_DISTRIBUTED2 InterpolatedVariable : public ReferenceCount {
PUBLISHED:
  INLINE InterpolatedVariable();

  INLINE bool record_value(const Type &value, double timestamp,
                           bool record_last_networked = true);

  INLINE void record_last_networked_value(const Type &value, double timestamp);

  INLINE void set_interpolation_amount(PN_stdfloat amount);
  INLINE PN_stdfloat get_interpolation_amount() const;

  INLINE void set_looping(bool loop);
  INLINE bool get_looping() const;

  INLINE void clear_history();
  INLINE void reset(const Type &value);

  INLINE int interpolate(double now);

  INLINE const Type &get_interpolated_value() const;
  INLINE double get_interpolated_time() const;

  INLINE const Type &get_last_networked_value() const;
  INLINE double get_last_networked_time() const;

  INLINE void get_derivative(Type *out, double now);
  INLINE void get_derivative_smooth_velocity(Type *out, double now);

  INLINE double get_interval() const;

private:
  INLINE void push_front(const Type &value, double timestamp, bool flush_newer);
  INLINE void remove_samples_before(double timestamp);

  class InterpolationInfo {
  public:
    bool hermite;
    int oldest; // Only set if using hermite interpolation.
    int older;
    int newer;
    double frac;
  };

  INLINE bool get_interpolation_info(InterpolationInfo &info, double now,
                                     int &no_more_changes) const;

private:
  typedef SamplePointBase<Type> SamplePoint;
  typedef pdeque<SamplePoint> SamplePoints;
  SamplePoints _sample_points;

  INLINE void time_fixup_hermite(SamplePoint &fixup, SamplePoint *&prev, SamplePoint *&start, SamplePoint *&end);
  INLINE void time_fixup2_hermite(SamplePoint &fixup, SamplePoint *&prev, SamplePoint *&start, double dt);
  INLINE void interpolate_hermite(Type *out, double frac, SamplePoint *prev, SamplePoint *start, SamplePoint *end, bool looping = false);
  INLINE void derivative_hermite(Type *out, double frac, SamplePoint *original_prev, SamplePoint *start, SamplePoint *end);
  INLINE void derivative_hermite_smooth_velocity(Type *out, double frac, SamplePoint *b, SamplePoint *c, SamplePoint *d);

  INLINE void interpolate(Type *out, double frac, SamplePoint *start, SamplePoint *end);
  INLINE void derivative_linear(Type *out, SamplePoint *start, SamplePoint *end);

  INLINE void extrapolate(Type *out, SamplePoint *old, SamplePoint *new_point, double dest_time, double max_extrapolate);

  // The most recently computed interpolated value.
  double _interpolated_value_time;
  Type _interpolated_value;

  // The most recently recorded sample point.
  Type _last_networked_value;
  double _last_networked_time;

  PN_stdfloat _interpolation_amount;
  bool _looping;
};

BEGIN_PUBLISH

typedef InterpolatedVariable<float> InterpolatedFloat;
typedef InterpolatedVariable<LVecBase2f> InterpolatedVec2f;
typedef InterpolatedVariable<LVecBase3f> InterpolatedVec3f;
typedef InterpolatedVariable<LVecBase4f> InterpolatedVec4f;

EXPORT_TEMPLATE_CLASS(EXPCL_DIRECT_DISTRIBUTED2, EXPTP_DIRECT_DISTRIBUTED2, InterpolatedVariable<float>);
EXPORT_TEMPLATE_CLASS(EXPCL_DIRECT_DISTRIBUTED2, EXPTP_DIRECT_DISTRIBUTED2, InterpolatedVariable<LVecBase2f>);
EXPORT_TEMPLATE_CLASS(EXPCL_DIRECT_DISTRIBUTED2, EXPTP_DIRECT_DISTRIBUTED2, InterpolatedVariable<LVecBase3f>);
EXPORT_TEMPLATE_CLASS(EXPCL_DIRECT_DISTRIBUTED2, EXPTP_DIRECT_DISTRIBUTED2, InterpolatedVariable<LVecBase4f>);

typedef InterpolatedVariable<double> InterpolatedDouble;
typedef InterpolatedVariable<LVecBase2d> InterpolatedVec2d;
typedef InterpolatedVariable<LVecBase3d> InterpolatedVec3d;
typedef InterpolatedVariable<LVecBase4d> InterpolatedVec4d;

EXPORT_TEMPLATE_CLASS(EXPCL_DIRECT_DISTRIBUTED2, EXPTP_DIRECT_DISTRIBUTED2, InterpolatedVariable<double>);
EXPORT_TEMPLATE_CLASS(EXPCL_DIRECT_DISTRIBUTED2, EXPTP_DIRECT_DISTRIBUTED2, InterpolatedVariable<LVecBase2d>);
EXPORT_TEMPLATE_CLASS(EXPCL_DIRECT_DISTRIBUTED2, EXPTP_DIRECT_DISTRIBUTED2, InterpolatedVariable<LVecBase3d>);
EXPORT_TEMPLATE_CLASS(EXPCL_DIRECT_DISTRIBUTED2, EXPTP_DIRECT_DISTRIBUTED2, InterpolatedVariable<LVecBase4d>);

#ifdef STDFLOAT_DOUBLE
typedef InterpolatedDouble InterpolatedSTDFloat;
typedef InterpolatedVec2d InterpolatedVec2;
typedef InterpolatedVec3d InterpolatedVec3;
typedef InterpolatedVec3d InterpolatedVec4;
#else
typedef InterpolatedFloat InterpolatedSTDFloat;
typedef InterpolatedVec2f InterpolatedVec2;
typedef InterpolatedVec3f InterpolatedVec3;
typedef InterpolatedVec3f InterpolatedVec4;
#endif

END_PUBLISH

#include "interpolatedVariable.I"

#endif // INTERPOLATEDVARIABLE_H
