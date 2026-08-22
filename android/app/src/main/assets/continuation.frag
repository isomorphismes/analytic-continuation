#version 300 es
precision highp float;
precision highp int;

#define MAX_ZEROS 32
#define LASSO_COEFFICIENT_COUNT 5

in vec2 v_ndc;
out vec4 frag_color;

uniform vec2 u_resolution;
uniform int u_zero_count;
uniform vec2 u_zero_preimages[MAX_ZEROS];
uniform vec2 u_zero_positions[MAX_ZEROS];
uniform vec2 u_lasso_coefficients[LASSO_COEFFICIENT_COUNT];
uniform float u_phase;
uniform int u_paused;

const float TAU = 6.28318530717958647692;
const float LOG_10 = 2.30258509299404568402;

vec2 complex_multiply(vec2 left, vec2 right) {
    return vec2(
        left.x * right.x - left.y * right.y,
        left.x * right.y + left.y * right.x
    );
}

vec2 complex_divide(vec2 numerator, vec2 denominator) {
    float scale = max(dot(denominator, denominator), 1.0e-10);
    return vec2(
        numerator.x * denominator.x + numerator.y * denominator.y,
        numerator.y * denominator.x - numerator.x * denominator.y
    ) / scale;
}

vec2 lasso_map_and_derivative(vec2 w, float amount, out vec2 derivative) {
    vec2 mapped = w;
    derivative = vec2(1.0, 0.0);
    vec2 power = w;

    for (int index = 0; index < LASSO_COEFFICIENT_COUNT; ++index) {
        float degree = float(index + 2);
        vec2 next_power = complex_multiply(power, w);
        vec2 coefficient = amount * u_lasso_coefficients[index];

        mapped += complex_multiply(coefficient, next_power);
        derivative += degree * complex_multiply(coefficient, power);
        power = next_power;
    }

    return mapped;
}

vec2 inverse_lasso(vec2 z) {
    // Continue the inverse from the identity map to the current lasso in four
    // small parameter steps. This gives a stable branch on both sides of the
    // white curve instead of clipping the exterior.
    vec2 w = z;

    for (int stage = 1; stage <= 4; ++stage) {
        float amount = 0.25 * float(stage);

        for (int iteration = 0; iteration < 2; ++iteration) {
            vec2 derivative;
            vec2 mapped = lasso_map_and_derivative(w, amount, derivative);
            vec2 correction = complex_divide(mapped - z, derivative);
            float correction_length = length(correction);
            if (correction_length > 0.55) {
                correction *= 0.55 / correction_length;
            }
            w -= correction;
        }
    }

    return w;
}

float positive_fract(float value) {
    return value - floor(value);
}

float srgb_component(float linear_value) {
    float value = max(linear_value, 0.0);
    if (value <= 0.0031308) {
        return 12.92 * value;
    }
    return 1.055 * pow(value, 1.0 / 2.4) - 0.055;
}

vec3 hcl_to_srgb(float hue_degrees, float chroma, float lightness) {
    float hue = radians(hue_degrees);
    float u_star = chroma * cos(hue);
    float v_star = chroma * sin(hue);

    const float white_u_prime = 0.19783982482140777;
    const float white_v_prime = 0.46833630293240974;

    float y = lightness > 8.0
        ? pow((lightness + 16.0) / 116.0, 3.0)
        : lightness / 903.2962962962963;

    float u_prime = u_star / (13.0 * lightness) + white_u_prime;
    float v_prime = v_star / (13.0 * lightness) + white_v_prime;

    float x = (9.0 * y * u_prime) / (4.0 * v_prime);
    float z = y * (12.0 - 3.0 * u_prime - 20.0 * v_prime) / (4.0 * v_prime);

    float linear_r =  3.2404542 * x - 1.5371385 * y - 0.4985314 * z;
    float linear_g = -0.9692660 * x + 1.8760108 * y + 0.0415560 * z;
    float linear_b =  0.0556434 * x - 0.2040259 * y + 1.0572252 * z;

    return clamp(vec3(
        srgb_component(linear_r),
        srgb_component(linear_g),
        srgb_component(linear_b)
    ), 0.0, 1.0);
}

float circle_mask(vec2 point, vec2 center, float radius) {
    return 1.0 - smoothstep(radius - 1.25, radius + 1.25, length(point - center));
}

float line_mask(vec2 point, vec2 start, vec2 finish, float half_width) {
    vec2 segment = finish - start;
    float denominator = max(dot(segment, segment), 1.0e-6);
    float along = clamp(dot(point - start, segment) / denominator, 0.0, 1.0);
    float distance_to_line = length(point - (start + along * segment));
    return 1.0 - smoothstep(half_width - 1.0, half_width + 1.0, distance_to_line);
}

void main() {
    float pixel_radius = 0.42 * min(u_resolution.x, u_resolution.y);
    vec2 pixel = gl_FragCoord.xy - 0.5 * u_resolution;
    vec2 z = pixel / pixel_radius;

    // w is the analytically continued inverse coordinate. The same domain
    // coloring is evaluated inside and outside the lasso.
    vec2 w = inverse_lasso(z);
    float w_radius = length(w);

    float phase = u_phase;
    float log_modulus = 0.0;

    for (int index = 0; index < MAX_ZEROS; ++index) {
        if (index >= u_zero_count) {
            break;
        }

        vec2 a = u_zero_preimages[index];
        vec2 numerator = w - a;

        // denominator = 1 - conjugate(a) * w
        vec2 denominator = vec2(
            1.0 - a.x * w.x - a.y * w.y,
            -a.x * w.y + a.y * w.x
        );

        phase += atan(numerator.y, numerator.x) - atan(denominator.y, denominator.x);
        log_modulus += log(max(length(numerator), 1.0e-12));
        log_modulus -= log(max(length(denominator), 1.0e-12));
    }

    float hue_degrees = 360.0 * positive_fract(phase / TAU);
    float log_modulus_band = positive_fract(log_modulus / LOG_10);
    float lightness = 66.0
        + 4.0 * log_modulus_band
        + 3.0 * positive_fract(hue_degrees / 100.0);
    vec3 color = hcl_to_srgb(hue_degrees, 45.0, lightness);

    // psi maps |w|=1 to the deformable lasso. Since every finite Blaschke
    // factor has modulus one on |w|=1, the white curve remains exactly
    // |f(z)|=1 after every accepted deformation.
    vec2 unit_w = w_radius > 1.0e-6 ? w / w_radius : vec2(1.0, 0.0);
    vec2 boundary_derivative;
    lasso_map_and_derivative(unit_w, 1.0, boundary_derivative);
    float edge_distance_pixels =
        abs(w_radius - 1.0) * max(length(boundary_derivative), 0.15) * pixel_radius;
    float boundary = 1.0 - smoothstep(1.2, 3.2, edge_distance_pixels);
    color = mix(color, vec3(0.97, 0.97, 0.94), boundary);

    // Zero markers stay fixed in physical z coordinates while the lasso moves.
    for (int index = 0; index < MAX_ZEROS; ++index) {
        if (index >= u_zero_count) {
            break;
        }
        float zero_distance_pixels = length(z - u_zero_positions[index]) * pixel_radius;
        float outer = 1.0 - smoothstep(7.0, 9.0, zero_distance_pixels);
        float inner = 1.0 - smoothstep(3.0, 4.5, zero_distance_pixels);
        color = mix(color, vec3(0.04), outer);
        color = mix(color, vec3(0.98), inner);
    }

    // Keep app controls clear of Android's right-edge navigation strip.
    float control_radius = clamp(0.052 * min(u_resolution.x, u_resolution.y), 28.0, 42.0);
    vec2 pause_center = vec2(
        control_radius + 16.0,
        u_resolution.y - control_radius - 16.0
    );
    vec2 close_center = vec2(
        u_resolution.x - 4.0 * control_radius - 16.0,
        u_resolution.y - control_radius - 16.0
    );
    float pause_disk = circle_mask(gl_FragCoord.xy, pause_center, control_radius);
    float close_disk = circle_mask(gl_FragCoord.xy, close_center, control_radius);
    color = mix(color, vec3(0.04), max(pause_disk, close_disk) * 0.78);

    float mark = 0.0;
    if (u_paused == 0) {
        mark = max(
            line_mask(
                gl_FragCoord.xy,
                pause_center + vec2(-8.0, -11.0),
                pause_center + vec2(-8.0, 11.0),
                2.2
            ),
            line_mask(
                gl_FragCoord.xy,
                pause_center + vec2(8.0, -11.0),
                pause_center + vec2(8.0, 11.0),
                2.2
            )
        );
    } else {
        vec2 left = pause_center + vec2(-8.0, -12.0);
        vec2 top = pause_center + vec2(11.0, 0.0);
        vec2 bottom = pause_center + vec2(-8.0, 12.0);
        mark = max(
            line_mask(gl_FragCoord.xy, left, top, 2.2),
            line_mask(gl_FragCoord.xy, top, bottom, 2.2)
        );
    }

    mark = max(
        mark,
        line_mask(
            gl_FragCoord.xy,
            close_center + vec2(-10.0, -10.0),
            close_center + vec2(10.0, 10.0),
            2.2
        )
    );
    mark = max(
        mark,
        line_mask(
            gl_FragCoord.xy,
            close_center + vec2(-10.0, 10.0),
            close_center + vec2(10.0, -10.0),
            2.2
        )
    );
    color = mix(color, vec3(0.98), mark);

    frag_color = vec4(color, 1.0);
}
