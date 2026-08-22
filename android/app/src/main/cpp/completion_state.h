#ifndef ANALYTIC_CONTINUATION_COMPLETION_STATE_H
#define ANALYTIC_CONTINUATION_COMPLETION_STATE_H

#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#define MAX_COMPLETION_COEFFICIENTS 8
#define MAX_VALUE_CONSTRAINTS 8

struct completion_state {
    float anchor[MAX_COMPLETION_COEFFICIENTS][2];
    float coefficients[MAX_COMPLETION_COEFFICIENTS][2];
    float wander[MAX_COMPLETION_COEFFICIENTS][2];
    float constraint_domains[MAX_VALUE_CONSTRAINTS][2];
    float constraint_values[MAX_VALUE_CONSTRAINTS][2];
    int constraint_count;
    uint32_t random_state;
};

static void completion_complex_multiply(
    const float left[2],
    const float right[2],
    float output[2]
) {
    float real = left[0] * right[0] - left[1] * right[1];
    float imaginary = left[0] * right[1] + left[1] * right[0];
    output[0] = real;
    output[1] = imaginary;
}

static bool completion_complex_divide(
    const float numerator[2],
    const float denominator[2],
    float output[2]
) {
    float squared_modulus =
        denominator[0] * denominator[0] +
        denominator[1] * denominator[1];
    if (squared_modulus < 1.0e-12f) {
        return false;
    }

    output[0] =
        (numerator[0] * denominator[0] + numerator[1] * denominator[1]) /
        squared_modulus;
    output[1] =
        (numerator[1] * denominator[0] - numerator[0] * denominator[1]) /
        squared_modulus;
    return true;
}

static void completion_evaluate_coefficients(
    float coefficients[MAX_COMPLETION_COEFFICIENTS][2],
    const float domain[2],
    float output[2]
) {
    float value[2] = {0.0f, 0.0f};

    for (int index = MAX_COMPLETION_COEFFICIENTS - 1; index >= 0; --index) {
        float multiplied[2];
        completion_complex_multiply(value, domain, multiplied);
        value[0] = multiplied[0] + coefficients[index][0];
        value[1] = multiplied[1] + coefficients[index][1];
    }

    output[0] = value[0];
    output[1] = value[1];
}

static void completion_vanishing_coefficients(
    const struct completion_state *state,
    float output[MAX_COMPLETION_COEFFICIENTS][2]
) {
    memset(output, 0, sizeof(float) * MAX_COMPLETION_COEFFICIENTS * 2);
    output[0][0] = 1.0f;
    int degree = 0;

    for (int constraint = 0; constraint < state->constraint_count; ++constraint) {
        float next[MAX_COMPLETION_COEFFICIENTS][2] = {{0.0f, 0.0f}};
        float negative_domain[2] = {
            -state->constraint_domains[constraint][0],
            -state->constraint_domains[constraint][1]
        };

        for (int coefficient = 0; coefficient <= degree; ++coefficient) {
            float constant_term[2];
            completion_complex_multiply(
                output[coefficient],
                negative_domain,
                constant_term
            );
            next[coefficient][0] += constant_term[0];
            next[coefficient][1] += constant_term[1];

            if (coefficient + 1 < MAX_COMPLETION_COEFFICIENTS) {
                next[coefficient + 1][0] += output[coefficient][0];
                next[coefficient + 1][1] += output[coefficient][1];
            }
        }

        memcpy(output, next, sizeof(next));
        ++degree;
    }
}

static void completion_reset_wander(struct completion_state *state) {
    memcpy(state->anchor, state->coefficients, sizeof(state->anchor));
    memset(state->wander, 0, sizeof(state->wander));
}

static void completion_state_initialize(
    struct completion_state *state,
    uint32_t random_seed
) {
    memset(state, 0, sizeof(*state));
    state->random_state = random_seed != 0u ? random_seed : 0x51f15e5du;

    state->coefficients[0][0] = 0.55f;
    state->coefficients[0][1] = 0.15f;
    state->coefficients[1][0] = 0.90f;
    state->coefficients[1][1] = 0.05f;
    state->coefficients[2][0] = 0.08f;
    state->coefficients[2][1] = -0.06f;
    memcpy(state->anchor, state->coefficients, sizeof(state->anchor));
}

static int completion_remaining_complex_dimensions(
    const struct completion_state *state
) {
    return MAX_COMPLETION_COEFFICIENTS - state->constraint_count;
}

static uint32_t completion_random_u32(struct completion_state *state) {
    uint32_t value = state->random_state;
    value ^= value << 13;
    value ^= value >> 17;
    value ^= value << 5;
    state->random_state = value != 0u ? value : 0x51f15e5du;
    return state->random_state;
}

static float completion_random_signed(struct completion_state *state) {
    uint32_t value = completion_random_u32(state);
    float unit = (float)(value & 0x00ffffffu) / (float)0x01000000u;
    return 2.0f * unit - 1.0f;
}

static bool completion_domain_is_new(
    const struct completion_state *state,
    const float domain[2]
) {
    for (int index = 0; index < state->constraint_count; ++index) {
        float delta_x = domain[0] - state->constraint_domains[index][0];
        float delta_y = domain[1] - state->constraint_domains[index][1];
        if (delta_x * delta_x + delta_y * delta_y < 1.0e-10f) {
            return false;
        }
    }
    return true;
}

static bool completion_constrain_value(
    struct completion_state *state,
    const float domain[2],
    const float target_value[2]
) {
    if (
        state->constraint_count >= MAX_VALUE_CONSTRAINTS ||
        !completion_domain_is_new(state, domain)
    ) {
        return false;
    }

    float current_value[2];
    completion_evaluate_coefficients(state->coefficients, domain, current_value);

    float vanishing[MAX_COMPLETION_COEFFICIENTS][2];
    completion_vanishing_coefficients(state, vanishing);

    float response[2];
    completion_evaluate_coefficients(vanishing, domain, response);

    float difference[2] = {
        target_value[0] - current_value[0],
        target_value[1] - current_value[1]
    };
    float correction_scale[2];
    if (!completion_complex_divide(difference, response, correction_scale)) {
        return false;
    }

    for (int index = 0; index < MAX_COMPLETION_COEFFICIENTS; ++index) {
        float correction[2];
        completion_complex_multiply(
            correction_scale,
            vanishing[index],
            correction
        );
        state->coefficients[index][0] += correction[0];
        state->coefficients[index][1] += correction[1];
    }

    int slot = state->constraint_count;
    state->constraint_domains[slot][0] = domain[0];
    state->constraint_domains[slot][1] = domain[1];
    state->constraint_values[slot][0] = target_value[0];
    state->constraint_values[slot][1] = target_value[1];
    ++state->constraint_count;
    completion_reset_wander(state);
    return true;
}

static bool completion_lock_current_value(
    struct completion_state *state,
    const float domain[2]
) {
    float value[2];
    completion_evaluate_coefficients(state->coefficients, domain, value);
    return completion_constrain_value(state, domain, value);
}

static bool completion_step(struct completion_state *state) {
    int free_count = completion_remaining_complex_dimensions(state);
    if (free_count <= 0) {
        return false;
    }

    float freedom_fraction =
        (float)free_count / (float)MAX_COMPLETION_COEFFICIENTS;
    float freedom_scale = sqrtf(freedom_fraction);

    for (int index = 0; index < MAX_COMPLETION_COEFFICIENTS; ++index) {
        if (index >= free_count) {
            state->wander[index][0] = 0.0f;
            state->wander[index][1] = 0.0f;
            continue;
        }

        float degree_scale = 1.0f / (float)(index + 1);
        float noise = 0.010f * freedom_scale * degree_scale;
        state->wander[index][0] =
            0.985f * state->wander[index][0] +
            noise * completion_random_signed(state);
        state->wander[index][1] =
            0.985f * state->wander[index][1] +
            noise * completion_random_signed(state);
    }

    float vanishing[MAX_COMPLETION_COEFFICIENTS][2];
    completion_vanishing_coefficients(state, vanishing);

    float perturbation[MAX_COMPLETION_COEFFICIENTS][2] = {{0.0f, 0.0f}};
    int vanishing_count = state->constraint_count + 1;
    for (int left = 0; left < vanishing_count; ++left) {
        for (int right = 0; right < free_count; ++right) {
            int output_index = left + right;
            if (output_index >= MAX_COMPLETION_COEFFICIENTS) {
                continue;
            }
            float product[2];
            completion_complex_multiply(
                vanishing[left],
                state->wander[right],
                product
            );
            perturbation[output_index][0] += product[0];
            perturbation[output_index][1] += product[1];
        }
    }

    for (int index = 0; index < MAX_COMPLETION_COEFFICIENTS; ++index) {
        state->coefficients[index][0] =
            state->anchor[index][0] + perturbation[index][0];
        state->coefficients[index][1] =
            state->anchor[index][1] + perturbation[index][1];
    }
    return true;
}

#endif
