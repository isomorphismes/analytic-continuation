#ifndef ANALYTIC_CONTINUATION_FIELD_EVOLUTION_H
#define ANALYTIC_CONTINUATION_FIELD_EVOLUTION_H

#include <stdbool.h>
#include <stdint.h>

#include "holomorphic_walk.h"

struct field_evolution {
    float coefficients[HOLOMORPHIC_WALK_COEFFICIENT_COUNT][2];
    float velocity[HOLOMORPHIC_WALK_COEFFICIENT_COUNT][2];
    float speed;
    float last_score;
    double last_time;
    double last_publish;
    uint64_t accepted_steps;
    bool workers_started;
    bool direction_ready;
};

void field_evolution_initialize(
    struct field_evolution *field,
    float speed,
    double now
);

bool field_evolution_start(struct field_evolution *field, double now);
void field_evolution_stop(struct field_evolution *field);
void field_evolution_reset_clock(struct field_evolution *field, double now);
void field_evolution_publish_now(struct field_evolution *field, double now);

bool field_evolution_advance(
    struct field_evolution *field,
    double now,
    bool allow_motion
);

#endif
