#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

#include "../android/app/src/main/cpp/completion_zero_one.h"

static float complex_distance(const float left[2], const float right[2]) {
    return hypotf(left[0] - right[0], left[1] - right[1]);
}

int main(void) {
    struct completion_state state;
    completion_state_initialize(&state, 11u);

    const float zero_domain[2] = {-0.75f, 0.20f};
    const float one_domain[2] = {0.90f, -0.15f};
    const float zero[2] = {0.0f, 0.0f};
    const float one[2] = {1.0f, 0.0f};

    assert(completion_constrain_zero_one_symbol(
        &state,
        zero_domain,
        one_domain
    ));
    assert(state.constraint_count == 2);
    assert(completion_remaining_complex_dimensions(&state) == 6);
    assert(complex_distance(state.constraint_values[0], zero) < 1.0e-7f);
    assert(complex_distance(state.constraint_values[1], one) < 1.0e-7f);

    for (int frame = 0; frame < 240; ++frame) {
        assert(completion_step(&state));
    }

    float zero_value[2];
    float one_value[2];
    completion_evaluate_coefficients(
        state.coefficients,
        zero_domain,
        zero_value
    );
    completion_evaluate_coefficients(
        state.coefficients,
        one_domain,
        one_value
    );
    assert(complex_distance(zero_value, zero) < 4.0e-4f);
    assert(complex_distance(one_value, one) < 4.0e-4f);

    struct completion_state before = state;
    assert(!completion_constrain_zero_one_symbol(
        &state,
        zero_domain,
        zero_domain
    ));
    assert(memcmp(&before, &state, sizeof(state)) == 0);

    const float repeated_one_domain[2] = {1.20f, 0.40f};
    before = state;
    assert(!completion_constrain_zero_one_symbol(
        &state,
        zero_domain,
        repeated_one_domain
    ));
    assert(memcmp(&before, &state, sizeof(state)) == 0);

    puts("zero_one_symbol: ok");
    return 0;
}
