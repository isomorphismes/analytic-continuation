#include <assert.h>
#include <math.h>
#include <stdio.h>

#include "../android/app/src/main/cpp/completion_state.h"

static float complex_distance(const float left[2], const float right[2]) {
    return hypotf(left[0] - right[0], left[1] - right[1]);
}

static void evaluate_at(
    const struct completion_state *state,
    float real,
    float imaginary,
    float output[2]
) {
    const float domain[2] = {real, imaginary};
    completion_evaluate(state, domain, output);
}

int main(void) {
    struct completion_state state;
    completion_state_initialize(&state, 7u);

    bool has_transcendental_mode = false;
    for (int mode = 1; mode < MAX_ANALYTIC_MODES; ++mode) {
        float frequency_squared =
            state.mode_frequencies[mode][0] * state.mode_frequencies[mode][0] +
            state.mode_frequencies[mode][1] * state.mode_frequencies[mode][1];
        float amplitude_squared =
            state.anchor_polynomials[mode][0][0] *
                state.anchor_polynomials[mode][0][0] +
            state.anchor_polynomials[mode][0][1] *
                state.anchor_polynomials[mode][0][1];
        if (frequency_squared > 1.0e-8f && amplitude_squared > 1.0e-10f) {
            has_transcendental_mode = true;
        }
    }
    assert(has_transcendental_mode);

    for (int frame = 0; frame < 30; ++frame) {
        assert(completion_step(&state));
    }

    float probes_before[3][2];
    evaluate_at(&state, -0.9f, 0.4f, probes_before[0]);
    evaluate_at(&state, 0.2f, -0.7f, probes_before[1]);
    evaluate_at(&state, 1.1f, 0.25f, probes_before[2]);

    const float lock_domain[2] = {0.4f, -0.3f};
    assert(completion_lock_current_value(&state, lock_domain));
    assert(state.constraint_count == 1);

    for (int probe = 0; probe < 3; ++probe) {
        const float domains[3][2] = {
            {-0.9f, 0.4f},
            {0.2f, -0.7f},
            {1.1f, 0.25f}
        };
        float after[2];
        completion_evaluate(&state, domains[probe], after);
        assert(complex_distance(probes_before[probe], after) < 3.0e-5f);
    }

    float locked_value[2];
    completion_evaluate(&state, lock_domain, locked_value);
    for (int frame = 0; frame < 240; ++frame) {
        assert(completion_step(&state));
    }
    float after_walk[2];
    completion_evaluate(&state, lock_domain, after_walk);
    assert(complex_distance(locked_value, after_walk) < 3.0e-4f);

    const float zero_domain[2] = {-0.8f, 0.2f};
    const float zero[2] = {0.0f, 0.0f};
    assert(completion_constrain_value(&state, zero_domain, zero));

    const float one_domain[2] = {0.9f, 0.15f};
    const float one[2] = {1.0f, 0.0f};
    assert(completion_constrain_value(&state, one_domain, one));

    for (int frame = 0; frame < 180; ++frame) {
        assert(completion_step(&state));
    }
    float zero_value[2];
    float one_value[2];
    completion_evaluate(&state, zero_domain, zero_value);
    completion_evaluate(&state, one_domain, one_value);
    assert(complex_distance(zero, zero_value) < 5.0e-4f);
    assert(complex_distance(one, one_value) < 5.0e-4f);

    float motion_before = completion_motion_scale(&state);
    const float more_domains[5][2] = {
        {-1.1f, -0.4f},
        {-0.4f, 0.9f},
        {0.1f, -0.8f},
        {0.6f, 0.75f},
        {1.2f, -0.55f}
    };
    for (int index = 0; index < 5; ++index) {
        assert(completion_lock_current_value(&state, more_domains[index]));
    }
    assert(state.constraint_count == 8);
    assert(completion_motion_scale(&state) < motion_before);

    float constraints_before[8][2];
    for (int index = 0; index < state.constraint_count; ++index) {
        completion_evaluate(
            &state,
            state.constraint_domains[index],
            constraints_before[index]
        );
    }

    float unconstrained_before[2];
    evaluate_at(&state, 0.33f, 0.61f, unconstrained_before);
    for (int frame = 0; frame < 180; ++frame) {
        assert(completion_step(&state));
    }
    float unconstrained_after[2];
    evaluate_at(&state, 0.33f, 0.61f, unconstrained_after);
    assert(complex_distance(unconstrained_before, unconstrained_after) > 1.0e-5f);

    for (int index = 0; index < state.constraint_count; ++index) {
        float after[2];
        completion_evaluate(&state, state.constraint_domains[index], after);
        assert(complex_distance(constraints_before[index], after) < 8.0e-4f);
    }

    assert(completion_constraint_slots_remaining(&state) == 4);
    puts("completion_state: ok");
    return 0;
}
