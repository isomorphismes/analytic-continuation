from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


c_path = Path("android/app/src/main/cpp/analytic_continuation_random.c")
source = c_path.read_text()
old_geometry = '''    float pixel_radius = view_pixel_radius(engine);\n    float view_outer_radius = hypotf(\n        0.5f * (float)engine->width,\n        0.5f * (float)engine->height\n    ) / pixel_radius;\n'''
new_geometry = '''    // Keep the wanderers in the mathematical plane. Zoom changes the view,\n    // not their coordinates. At zoom 1 this matches the established orbit scale.\n    float base_pixel_radius = 0.42f * fminf(\n        (float)engine->width, (float)engine->height\n    );\n    float world_outer_radius = hypotf(\n        0.5f * (float)engine->width,\n        0.5f * (float)engine->height\n    ) / base_pixel_radius;\n'''
source = replace_once(source, old_geometry, new_geometry, "remote orbit geometry")
source = source.replace(
    "positions[index][0] = view_outer_radius * radius",
    "positions[index][0] = world_outer_radius * radius",
)
source = source.replace(
    "positions[index][1] = view_outer_radius * radius",
    "positions[index][1] = world_outer_radius * radius",
)
if "view_outer_radius * radius" in source:
    raise SystemExit("old viewport-relative remote orbit scale remains")
c_path.write_text(source)

shader_path = Path("android/app/src/main/assets/continuation.frag.in")
shader = shader_path.read_text()
old_init = '''    float phase = 0.0;\n    float log_modulus = 0.0;\n\n    // R(z): the explicit meromorphic divisor on the ordinary complex plane.\n'''
new_init = '''    // H(z) = exp(q(z)) is entire and nonzero. Wegert coloring only uses\n    // phase modulo tau and log-modulus modulo log(10), so reduce the large\n    // entire contribution before adding the explicit divisor. This prevents\n    // far-zoom fp32 cancellation from making user zeros/poles numerically vanish.\n    vec2 q = holomorphic_q(z);\n    float phase = q.y - WEGERT_TAU * floor(q.y / WEGERT_TAU);\n    float log_modulus = q.x - WEGERT_LOG_10 * floor(q.x / WEGERT_LOG_10);\n\n    // R(z): the explicit meromorphic divisor on the ordinary complex plane.\n'''
shader = replace_once(shader, old_init, new_init, "phase/log initialization")
old_q = '''    // H(z) = exp(q(z)) is entire and nonzero, so it changes neither zeros nor\n    // poles. Re(q) adds to log modulus and Im(q) adds to phase exactly.\n    vec2 q = holomorphic_q(z);\n    log_modulus += q.x;\n    phase += q.y;\n\n'''
shader = replace_once(shader, old_q, "", "late q accumulation")

user_pole_end = '''        color = mix(color, vec3(0.04), pole_mark);\n    }\n\n    float placement_radius = clamp(0.048 * min(u_resolution.x, u_resolution.y), 26.0, 38.0);\n'''
remote_overlay = '''        color = mix(color, vec3(0.04), pole_mark);\n    }\n\n    // Remote poles are persistent mathematical poles. Draw their X markers\n    // when zoom brings them into the viewport, without making them editable.\n    // Use a cheap diagonal-distance mask so the phone fast path stays light.\n    for (int index = 0; index < REMOTE_POLE_COUNT; ++index) {\n        vec2 center = 0.5 * u_resolution\n            + u_remote_pole_positions[index] * pixel_radius;\n        if (\n            center.x < -10.0 || center.x > u_resolution.x + 10.0 ||\n            center.y < -10.0 || center.y > u_resolution.y + 10.0\n        ) {\n            continue;\n        }\n        vec2 offset = abs(gl_FragCoord.xy - center);\n        float extent = max(offset.x, offset.y);\n        float diagonal = abs(offset.x - offset.y);\n        float remote_mark =\n            (1.0 - smoothstep(1.4, 2.6, diagonal)) *\n            (1.0 - smoothstep(7.0, 8.5, extent));\n        color = mix(color, vec3(0.04), remote_mark);\n    }\n\n    float placement_radius = clamp(0.048 * min(u_resolution.x, u_resolution.y), 26.0, 38.0);\n'''
shader = replace_once(shader, user_pole_end, remote_overlay, "remote pole overlay insertion")
shader_path.write_text(shader)
