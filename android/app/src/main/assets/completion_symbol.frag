#version 300 es
precision highp float;
precision highp int;

#define MAX_COMPLETION_COEFFICIENTS 8
#define MAX_VALUE_CONSTRAINTS 8

in vec2 v_ndc;
out vec4 frag_color;

uniform vec2 u_center;
uniform float u_half_height;
uniform float u_aspect;
uniform vec2 u_resolution;
uniform vec2 u_completion_coefficients[MAX_COMPLETION_COEFFICIENTS];
uniform int u_constraint_count;
uniform vec2 u_constraint_domains[MAX_VALUE_CONSTRAINTS];
uniform vec2 u_constraint_values[MAX_VALUE_CONSTRAINTS];
uniform int u_preview_active;
uniform vec2 u_preview_zero_domain;
uniform vec2 u_preview_one_domain;

const float TAU = 6.28318530717958647692;
const float LOG_10 = 2.30258509299404568402;

vec2 complex_multiply(vec2 left, vec2 right) {
    return vec2(
        left.x * right.x - left.y * right.y,
        left.x * right.y + left.y * right.x
    );
}

vec2 evaluate_completion(vec2 z) {
    vec2 value = vec2(0.0);
    for (int index = MAX_COMPLETION_COEFFICIENTS - 1; index >= 0; --index) {
        value = complex_multiply(value, z) + u_completion_coefficients[index];
    }
    return value;
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

bool is_zero_value(vec2 value) {
    return dot(value, value) < 1.0e-8;
}

bool is_one_value(vec2 value) {
    vec2 difference = value - vec2(1.0, 0.0);
    return dot(difference, difference) < 1.0e-8;
}

float segment_distance_pixels(
    vec2 point,
    vec2 start,
    vec2 finish,
    float world_per_pixel
) {
    vec2 segment = finish - start;
    float squared_length = max(dot(segment, segment), 1.0e-12);
    float along = clamp(dot(point - start, segment) / squared_length, 0.0, 1.0);
    return length(point - (start + along * segment)) / world_per_pixel;
}

void draw_zero_one_symbol(
    inout vec3 color,
    vec2 point,
    vec2 zero_domain,
    vec2 one_domain,
    float world_per_pixel
) {
    float line_distance = segment_distance_pixels(
        point,
        zero_domain,
        one_domain,
        world_per_pixel
    );
    float zero_distance = length(point - zero_domain) / world_per_pixel;

    float dark_line = 1.0 - smoothstep(4.2, 5.2, line_distance);
    float dark_dot = 1.0 - smoothstep(8.0, 9.0, zero_distance);
    color = mix(color, vec3(0.04), max(dark_line, dark_dot));

    float light_line = 1.0 - smoothstep(2.0, 2.8, line_distance);
    float light_dot = 1.0 - smoothstep(5.4, 6.4, zero_distance);
    color = mix(color, vec3(0.97, 0.96, 0.92), max(light_line, light_dot));
}

bool constraint_is_in_zero_one_symbol(int index) {
    if (
        index + 1 < u_constraint_count &&
        is_zero_value(u_constraint_values[index]) &&
        is_one_value(u_constraint_values[index + 1])
    ) {
        return true;
    }
    if (
        index > 0 &&
        is_zero_value(u_constraint_values[index - 1]) &&
        is_one_value(u_constraint_values[index])
    ) {
        return true;
    }
    return false;
}

void main() {
    vec2 z = u_center + vec2(
        v_ndc.x * u_half_height * u_aspect,
        v_ndc.y * u_half_height
    );
    vec2 value = evaluate_completion(z);

    float phase = atan(value.y, value.x);
    float log_modulus = log(max(length(value), 1.0e-12));
    float hue_degrees = 360.0 * positive_fract(phase / TAU);
    float log_modulus_band = positive_fract(log_modulus / LOG_10);
    float lightness = 66.0
        + 4.0 * log_modulus_band
        + 3.0 * positive_fract(hue_degrees / 100.0);
    vec3 color = hcl_to_srgb(hue_degrees, 45.0, lightness);

    float world_per_pixel = (2.0 * u_half_height) / max(u_resolution.y, 1.0);

    for (int index = 0; index < MAX_VALUE_CONSTRAINTS; ++index) {
        if (index >= u_constraint_count) {
            break;
        }
        if (constraint_is_in_zero_one_symbol(index)) {
            continue;
        }
        float radius = length(z - u_constraint_domains[index]) / world_per_pixel;
        float outer = 1.0 - smoothstep(6.0, 7.5, radius);
        float inner = 1.0 - smoothstep(3.2, 4.3, radius);
        float ring = max(0.0, outer - inner);
        color = mix(color, vec3(0.96, 0.95, 0.92), ring);
    }

    for (int index = 0; index < MAX_VALUE_CONSTRAINTS - 1; ++index) {
        if (index + 1 >= u_constraint_count) {
            break;
        }
        if (
            is_zero_value(u_constraint_values[index]) &&
            is_one_value(u_constraint_values[index + 1])
        ) {
            draw_zero_one_symbol(
                color,
                z,
                u_constraint_domains[index],
                u_constraint_domains[index + 1],
                world_per_pixel
            );
        }
    }

    if (u_preview_active != 0) {
        draw_zero_one_symbol(
            color,
            z,
            u_preview_zero_domain,
            u_preview_one_domain,
            world_per_pixel
        );
    }

    frag_color = vec4(color, 1.0);
}
