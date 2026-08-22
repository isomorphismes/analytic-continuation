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

    struct completion_state tap_state;
    completion_state_initialize(&tap_state, 13u);
    const float tap_domain[2] = {0.25f, -0.35f};
    assert(completion_lock_current_value(&tap_state, tap_domain));

    const float zero_domain[2] = {-0.75f, 0.20f};
    const float one_domain[2] = {0.90f, -0.15f};
    const float zero[2] = {0.0f, 0.0f};
    const float one[2] = {1.0f, 0.0f};

    assert(completion_constrain_zero_one_symbol(&state, zero_domain, one_domain));
    assert(state.constraint_count == 2);

    for (int frame = 0; frame < 180; ++frame) {
        assert(completion_step(&state));
    }

    float actual_zero[2];
    float actual_one[2];
    completion_evaluate(&state, zero_domain, actual_zero);
    completion_evaluate(&state, one_domain, actual_one);
    assert(complex_distance(actual_zero, zero) < 5.0e-4f);
    assert(complex_distance(actual_one, one) < 5.0e-4f);

    struct completion_state before = state;
    assert(!completion_constrain_zero_one_symbol(&state, zero_domain, one_domain));
    assert(memcmp(&before, &state, sizeof(state)) == 0);

    const float same[2] = {0.1f, 0.1f};
    before = state;
    assert(!completion_constrain_zero_one_symbol(&state, same, same));
    assert(memcmp(&before, &state, sizeof(state)) == 0);

    puts("zero_one_symbol: ok");
    return 0;
}
