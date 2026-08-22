#ifndef ANALYTIC_CONTINUATION_COMPLETION_ZERO_ONE_H
#define ANALYTIC_CONTINUATION_COMPLETION_ZERO_ONE_H

#include "completion_state.h"

static bool completion_constrain_zero_one_symbol(
    struct completion_state *state,
    const float zero_domain[2],
    const float one_domain[2]
) {
    if (completion_remaining_complex_dimensions(state) < 2) {
        return false;
    }

    float delta_x = one_domain[0] - zero_domain[0];
    float delta_y = one_domain[1] - zero_domain[1];
    if (delta_x * delta_x + delta_y * delta_y < 1.0e-10f) {
        return false;
    }

    struct completion_state before = *state;
    const float zero[2] = {0.0f, 0.0f};
    const float one[2] = {1.0f, 0.0f};

    if (
        !completion_constrain_value(state, zero_domain, zero) ||
        !completion_constrain_value(state, one_domain, one)
    ) {
        *state = before;
        return false;
    }

    return true;
}

#endif
