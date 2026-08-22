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
        float radius = length(z - u_constraint_domains[index]) / world_per_pixel;
        float outer = 1.0 - smoothstep(6.0, 7.5, radius);
        float inner = 1.0 - smoothstep(3.2, 4.3, radius);
        float ring = max(0.0, outer - inner);
        color = mix(color, vec3(0.96, 0.95, 0.92), ring);
    }

    frag_color = vec4(color, 1.0);
}
