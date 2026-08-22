#include <assert.h>
#include <math.h>
#include <stdio.h>

#include "../android/app/src/main/cpp/completion_state.h"

static float complex_distance(const float left[2], const float right[2]) {
    return hypotf(left[0] - right[0], left[1] - right[1]);
}

int main(void) {
    struct completion_state state;
    completion_state_initialize(&state, 7u);

    float lock_domain[2] = {0.4f, -0.3f};
    float before[MAX_COMPLETION_COEFFICIENTS][2];
    memcpy(before, state.coefficients, sizeof(before));

    assert(completion_lock_current_value(&state, lock_domain));
    assert(completion_remaining_complex_dimensions(&state) == 7);
    for (int index = 0; index < MAX_COMPLETION_COEFFICIENTS; ++index) {
        assert(fabsf(before[index][0] - state.coefficients[index][0]) < 1.0e-6f);
        assert(fabsf(before[index][1] - state.coefficients[index][1]) < 1.0e-6f);
    }

    float locked_value[2];
    completion_evaluate_coefficients(state.coefficients, lock_domain, locked_value);
    for (int frame = 0; frame < 240; ++frame) {
        assert(completion_step(&state));
    }
    float after_walk[2];
    completion_evaluate_coefficients(state.coefficients, lock_domain, after_walk);
    assert(complex_distance(locked_value, after_walk) < 2.0e-4f);

    float zero_domain[2] = {-0.8f, 0.2f};
    float zero[2] = {0.0f, 0.0f};
    assert(completion_constrain_value(&state, zero_domain, zero));
    float zero_value[2];
    completion_evaluate_coefficients(state.coefficients, zero_domain, zero_value);
    assert(complex_distance(zero, zero_value) < 2.0e-4f);

    float one_domain[2] = {0.9f, 0.15f};
    float one[2] = {1.0f, 0.0f};
    assert(completion_constrain_value(&state, one_domain, one));

    for (int frame = 0; frame < 180; ++frame) {
        assert(completion_step(&state));
    }
    completion_evaluate_coefficients(state.coefficients, zero_domain, zero_value);
    float one_value[2];
    completion_evaluate_coefficients(state.coefficients, one_domain, one_value);
    assert(complex_distance(zero, zero_value) < 4.0e-4f);
    assert(complex_distance(one, one_value) < 4.0e-4f);

    float more_domains[5][2] = {
        {-1.1f, -0.4f},
        {-0.4f, 0.9f},
        {0.1f, -0.8f},
        {0.6f, 0.75f},
        {1.2f, -0.55f}
    };
    for (int index = 0; index < 5; ++index) {
        assert(completion_lock_current_value(&state, more_domains[index]));
    }
    assert(completion_remaining_complex_dimensions(&state) == 0);

    float frozen[MAX_COMPLETION_COEFFICIENTS][2];
    memcpy(frozen, state.coefficients, sizeof(frozen));
    assert(!completion_step(&state));
    for (int index = 0; index < MAX_COMPLETION_COEFFICIENTS; ++index) {
        assert(frozen[index][0] == state.coefficients[index][0]);
        assert(frozen[index][1] == state.coefficients[index][1]);
    }

    puts("completion_state: ok");
    return 0;
}
