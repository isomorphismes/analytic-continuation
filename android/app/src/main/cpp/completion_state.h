#ifndef ANALYTIC_CONTINUATION_COMPLETION_STATE_H
#define ANALYTIC_CONTINUATION_COMPLETION_STATE_H

#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#define MAX_ANALYTIC_MODES 4
#define MAX_VALUE_CONSTRAINTS 12
#define MAX_ANCHOR_COEFFICIENTS (MAX_VALUE_CONSTRAINTS + 1)
#define COMPLETION_CONSTRAINT_SCALE 1.0f

struct completion_state {
    float mode_frequencies[MAX_ANALYTIC_MODES][2];
    float anchor_polynomials[MAX_ANALYTIC_MODES][MAX_ANCHOR_COEFFICIENTS][2];
    float wander[MAX_ANALYTIC_MODES][2];
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

static void completion_complex_exp(
    const float value[2],
    float output[2]
) {
    float modulus = expf(value[0]);
    output[0] = modulus * cosf(value[1]);
    output[1] = modulus * sinf(value[1]);
}

static uint32_t completion_random_u32(struct completion_state *state) {
    uint32_t value = state->random_state;
    value ^= value << 13;
    value ^= value >> 17;
    value ^= value << 5;
    state->random_state = value != 0u ? value : 0x51f15e5du;
    return state->random_state;
}

static float completion_random_unit(struct completion_state *state) {
    uint32_t value = completion_random_u32(state);
    return (float)(value & 0x00ffffffu) / (float)0x01000000u;
}

static float completion_random_signed(struct completion_state *state) {
    return 2.0f * completion_random_unit(state) - 1.0f;
}

static void completion_evaluate_polynomial(
    const float coefficients[MAX_ANCHOR_COEFFICIENTS][2],
    const float domain[2],
    float output[2]
) {
    float value[2] = {0.0f, 0.0f};

    for (int index = MAX_ANCHOR_COEFFICIENTS - 1; index >= 0; --index) {
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
    float output[MAX_ANCHOR_COEFFICIENTS][2]
) {
    memset(output, 0, sizeof(float) * MAX_ANCHOR_COEFFICIENTS * 2);
    output[0][0] = 1.0f;
    int degree = 0;

    for (int constraint = 0; constraint < state->constraint_count; ++constraint) {
        float next[MAX_ANCHOR_COEFFICIENTS][2] = {{0.0f, 0.0f}};
        float constant_term_factor[2] = {
            -state->constraint_domains[constraint][0] / COMPLETION_CONSTRAINT_SCALE,
            -state->constraint_domains[constraint][1] / COMPLETION_CONSTRAINT_SCALE
        };
        const float linear_term_factor[2] = {
            1.0f / COMPLETION_CONSTRAINT_SCALE,
            0.0f
        };

        for (int coefficient = 0; coefficient <= degree; ++coefficient) {
            float constant_term[2];
            completion_complex_multiply(
                output[coefficient],
                constant_term_factor,
                constant_term
            );
            next[coefficient][0] += constant_term[0];
            next[coefficient][1] += constant_term[1];

            float linear_term[2];
            completion_complex_multiply(
                output[coefficient],
                linear_term_factor,
                linear_term
            );
            next[coefficient + 1][0] += linear_term[0];
            next[coefficient + 1][1] += linear_term[1];
        }

        memcpy(output, next, sizeof(next));
        ++degree;
    }
}

static void completion_evaluate_vanishing(
    const struct completion_state *state,
    const float domain[2],
    float output[2]
) {
    float value[2] = {1.0f, 0.0f};

    for (int index = 0; index < state->constraint_count; ++index) {
        float factor[2] = {
            (domain[0] - state->constraint_domains[index][0]) /
                COMPLETION_CONSTRAINT_SCALE,
            (domain[1] - state->constraint_domains[index][1]) /
                COMPLETION_CONSTRAINT_SCALE
        };
        float product[2];
        completion_complex_multiply(value, factor, product);
        value[0] = product[0];
        value[1] = product[1];
    }

    output[0] = value[0];
    output[1] = value[1];
}

static void completion_mode_exponential(
    const struct completion_state *state,
    int mode,
    const float domain[2],
    float output[2]
) {
    float argument[2];
    completion_complex_multiply(state->mode_frequencies[mode], domain, argument);
    completion_complex_exp(argument, output);
}

static void completion_evaluate_anchor(
    const struct completion_state *state,
    const float domain[2],
    float output[2]
) {
    float value[2] = {0.0f, 0.0f};

    for (int mode = 0; mode < MAX_ANALYTIC_MODES; ++mode) {
        float polynomial[2];
        completion_evaluate_polynomial(
            state->anchor_polynomials[mode],
            domain,
            polynomial
        );
        float exponential[2];
        completion_mode_exponential(state, mode, domain, exponential);
        float term[2];
        completion_complex_multiply(polynomial, exponential, term);
        value[0] += term[0];
        value[1] += term[1];
    }

    output[0] = value[0];
    output[1] = value[1];
}

static void completion_evaluate(
    const struct completion_state *state,
    const float domain[2],
    float output[2]
) {
    float value[2];
    completion_evaluate_anchor(state, domain, value);

    float vanishing[2];
    completion_evaluate_vanishing(state, domain, vanishing);

    float wander_sum[2] = {0.0f, 0.0f};
    for (int mode = 0; mode < MAX_ANALYTIC_MODES; ++mode) {
        float exponential[2];
        completion_mode_exponential(state, mode, domain, exponential);
        float term[2];
        completion_complex_multiply(state->wander[mode], exponential, term);
        wander_sum[0] += term[0];
        wander_sum[1] += term[1];
    }

    float perturbation[2];
    completion_complex_multiply(vanishing, wander_sum, perturbation);
    output[0] = value[0] + perturbation[0];
    output[1] = value[1] + perturbation[1];
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

static int completion_constraint_slots_remaining(
    const struct completion_state *state
) {
    return MAX_VALUE_CONSTRAINTS - state->constraint_count;
}

static float completion_motion_scale(
    const struct completion_state *state
) {
    return 1.0f / sqrtf(1.0f + 0.55f * (float)state->constraint_count);
}

static void completion_commit_wander(struct completion_state *state) {
    float vanishing[MAX_ANCHOR_COEFFICIENTS][2];
    completion_vanishing_coefficients(state, vanishing);

    for (int mode = 0; mode < MAX_ANALYTIC_MODES; ++mode) {
        for (int coefficient = 0;
             coefficient < MAX_ANCHOR_COEFFICIENTS;
             ++coefficient) {
            float addition[2];
            completion_complex_multiply(
                state->wander[mode],
                vanishing[coefficient],
                addition
            );
            state->anchor_polynomials[mode][coefficient][0] += addition[0];
            state->anchor_polynomials[mode][coefficient][1] += addition[1];
        }
        state->wander[mode][0] = 0.0f;
        state->wander[mode][1] = 0.0f;
    }
}

static void completion_state_initialize(
    struct completion_state *state,
    uint32_t random_seed
) {
    memset(state, 0, sizeof(*state));
    state->random_state = random_seed != 0u ? random_seed : 0x51f15e5du;

    state->mode_frequencies[0][0] = 0.0f;
    state->mode_frequencies[0][1] = 0.0f;

    for (int mode = 1; mode < MAX_ANALYTIC_MODES; ++mode) {
        float angle = 6.28318530717958647692f * completion_random_unit(state);
        float magnitude = 0.055f + 0.035f * completion_random_unit(state);
        state->mode_frequencies[mode][0] = magnitude * cosf(angle);
        state->mode_frequencies[mode][1] = magnitude * sinf(angle);
    }

    state->anchor_polynomials[0][0][0] = 0.55f;
    state->anchor_polynomials[0][0][1] = 0.15f;
    state->anchor_polynomials[0][1][0] = 0.90f;
    state->anchor_polynomials[0][1][1] = 0.05f;
    state->anchor_polynomials[0][2][0] = 0.08f;
    state->anchor_polynomials[0][2][1] = -0.06f;

    for (int mode = 1; mode < MAX_ANALYTIC_MODES; ++mode) {
        float scale = 0.075f / (float)mode;
        state->anchor_polynomials[mode][0][0] =
            scale * completion_random_signed(state);
        state->anchor_polynomials[mode][0][1] =
            scale * completion_random_signed(state);
    }
}

static bool completion_constrain_value(
    struct completion_state *state,
    const float domain[2],
    const float target_value[2]
) {
    if (
        completion_constraint_slots_remaining(state) <= 0 ||
        !completion_domain_is_new(state, domain)
    ) {
        return false;
    }

    float current_value[2];
    completion_evaluate(state, domain, current_value);

    float vanishing_at_domain[2];
    completion_evaluate_vanishing(state, domain, vanishing_at_domain);
    if (
        vanishing_at_domain[0] * vanishing_at_domain[0] +
        vanishing_at_domain[1] * vanishing_at_domain[1] < 1.0e-12f
    ) {
        return false;
    }

    completion_commit_wander(state);

    float difference[2] = {
        target_value[0] - current_value[0],
        target_value[1] - current_value[1]
    };
    float correction_scale[2];
    if (!completion_complex_divide(
            difference,
            vanishing_at_domain,
            correction_scale
        )) {
        return false;
    }

    float vanishing_coefficients[MAX_ANCHOR_COEFFICIENTS][2];
    completion_vanishing_coefficients(state, vanishing_coefficients);
    for (int coefficient = 0;
         coefficient < MAX_ANCHOR_COEFFICIENTS;
         ++coefficient) {
        float correction[2];
        completion_complex_multiply(
            correction_scale,
            vanishing_coefficients[coefficient],
            correction
        );
        state->anchor_polynomials[0][coefficient][0] += correction[0];
        state->anchor_polynomials[0][coefficient][1] += correction[1];
    }

    int slot = state->constraint_count;
    state->constraint_domains[slot][0] = domain[0];
    state->constraint_domains[slot][1] = domain[1];
    state->constraint_values[slot][0] = target_value[0];
    state->constraint_values[slot][1] = target_value[1];
    ++state->constraint_count;
    return true;
}

static bool completion_lock_current_value(
    struct completion_state *state,
    const float domain[2]
) {
    float value[2];
    completion_evaluate(state, domain, value);
    return completion_constrain_value(state, domain, value);
}

static bool completion_step(struct completion_state *state) {
    float motion_scale = completion_motion_scale(state);

    for (int mode = 0; mode < MAX_ANALYTIC_MODES; ++mode) {
        float mode_scale = 1.0f / sqrtf((float)(mode + 1));
        float noise = 0.0085f * motion_scale * mode_scale;
        state->wander[mode][0] =
            0.985f * state->wander[mode][0] +
            noise * completion_random_signed(state);
        state->wander[mode][1] =
            0.985f * state->wander[mode][1] +
            noise * completion_random_signed(state);
    }

    return true;
}

#endif
