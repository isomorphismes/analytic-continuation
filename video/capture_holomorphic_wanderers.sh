#!/usr/bin/env bash
set -euo pipefail

# Presentation build derived from the tagged holomorphic explorer. The app itself
# owns both the live holomorphic soup and the divisor trajectories. The capture
# contains only the mathematical visualization: no generated/interpolated frames,
# no adb-driven marker motion, no app controls, and no Android system chrome.
python3 - <<'PY'
from pathlib import Path

path = Path('android/app/src/main/cpp/analytic_continuation_random.c')
text = path.read_text()

old = '''    bool deformation_workers_started;\n    bool deformation_direction_ready;\n    bool focused;\n'''
new = '''    bool deformation_workers_started;\n    bool deformation_direction_ready;\n    bool focused;\n    double wander_start_time;\n    bool wander_complete_logged;\n'''
if text.count(old) != 1:
    raise SystemExit('could not patch wander state fields')
text = text.replace(old, new, 1)

old = '''    engine->zero_count = 1;\n    engine->zero_positions[0][0] = -0.34f;\n    engine->zero_positions[0][1] = 0.0f;\n\n    engine->pole_count = 1;\n    engine->pole_positions[0][0] = 0.34f;\n    engine->pole_positions[0][1] = 0.0f;\n'''
new = '''    engine->zero_count = 3;\n    engine->zero_positions[0][0] = -0.65f;\n    engine->zero_positions[0][1] = 0.25f;\n    engine->zero_positions[1][0] = -0.15f;\n    engine->zero_positions[1][1] = -0.55f;\n    engine->zero_positions[2][0] = 0.50f;\n    engine->zero_positions[2][1] = 0.38f;\n\n    engine->pole_count = 3;\n    engine->pole_positions[0][0] = 0.65f;\n    engine->pole_positions[0][1] = -0.20f;\n    engine->pole_positions[1][0] = 0.10f;\n    engine->pole_positions[1][1] = 0.55f;\n    engine->pole_positions[2][0] = -0.45f;\n    engine->pole_positions[2][1] = -0.25f;\n'''
if text.count(old) != 1:
    raise SystemExit('could not patch initial divisor')
text = text.replace(old, new, 1)

old = '''    engine->deformation_direction_ready = false;\n    engine->focused = false;\n\n    engine->zoom = 1.0f;\n'''
new = '''    engine->deformation_direction_ready = false;\n    engine->focused = false;\n    engine->wander_start_time = 0.0;\n    engine->wander_complete_logged = false;\n\n    engine->zoom = 1.0f;\n'''
if text.count(old) != 1:
    raise SystemExit('could not patch wander initialization')
text = text.replace(old, new, 1)

marker = '''static void draw_frame(struct engine *engine) {\n'''
insert = r'''static float wander_smoothstep(float value) {
    if (value <= 0.0f) return 0.0f;
    if (value >= 1.0f) return 1.0f;
    return value * value * (3.0f - 2.0f * value);
}

static void wander_point(
    float output[2],
    const float start[2],
    const float finish[2],
    const float arc[2],
    float progress
) {
    const float pi = 3.14159265358979323846f;
    float bow = sinf(pi * progress);
    float meander = sinf(2.0f * pi * progress);

    output[0] =
        start[0] + (finish[0] - start[0]) * progress +
        arc[0] * bow - 0.10f * arc[1] * meander;
    output[1] =
        start[1] + (finish[1] - start[1]) * progress +
        arc[1] * bow + 0.10f * arc[0] * meander;
}

static void advance_wandering_divisor(struct engine *engine) {
    static const float zero_start[3][2] = {
        {-0.65f,  0.25f},
        {-0.15f, -0.55f},
        { 0.50f,  0.38f}
    };
    static const float zero_finish[3][2] = {
        { 0.65f, -0.20f},
        { 0.10f,  0.55f},
        {-0.45f, -0.25f}
    };
    static const float zero_arc[3][2] = {
        { 0.10f,  0.52f},
        { 0.50f,  0.08f},
        {-0.18f,  0.46f}
    };

    static const float pole_start[3][2] = {
        { 0.65f, -0.20f},
        { 0.10f,  0.55f},
        {-0.45f, -0.25f}
    };
    static const float pole_finish[3][2] = {
        {-0.65f,  0.25f},
        {-0.15f, -0.55f},
        { 0.50f,  0.38f}
    };
    static const float pole_arc[3][2] = {
        {-0.06f, -0.50f},
        {-0.48f, -0.06f},
        { 0.16f, -0.43f}
    };

    double now = monotonic_seconds();
    if (engine->wander_start_time <= 0.0) {
        engine->wander_start_time = now;
    }

    /* Let the stronger holomorphic soup establish itself, then wander for 16 s. */
    float raw = (float)((now - engine->wander_start_time - 4.0) / 16.0);
    float progress = wander_smoothstep(raw);

    for (int index = 0; index < 3; ++index) {
        wander_point(
            engine->zero_positions[index],
            zero_start[index],
            zero_finish[index],
            zero_arc[index],
            progress
        );
        wander_point(
            engine->pole_positions[index],
            pole_start[index],
            pole_finish[index],
            pole_arc[index],
            progress
        );
    }

    engine->dirty = true;
    if (raw >= 1.0f && !engine->wander_complete_logged) {
        LOGI("smooth divisor exchange complete: zeros=3 poles=3");
        engine->wander_complete_logged = true;
    }
}

'''
if text.count(marker) != 1:
    raise SystemExit('could not locate draw_frame insertion point')
text = text.replace(marker, insert + marker, 1)

old = '''        if (engine.display != EGL_NO_DISPLAY && engine.focused) {\n            advance_holomorphic_function(&engine);\n        }\n'''
new = '''        if (engine.display != EGL_NO_DISPLAY && engine.focused) {\n            advance_holomorphic_function(&engine);\n            advance_wandering_divisor(&engine);\n        }\n'''
if text.count(old) != 1:
    raise SystemExit('could not patch animation loop')
text = text.replace(old, new, 1)
path.write_text(text)

# Presentation shader: retain the real mathematical renderer and marker overlays,
# but suppress the two placement buttons. Keep u_placement_kind live so the native
# uniform contract remains unchanged.
shader_path = Path('android/app/src/main/assets/continuation.frag.in')
shader = shader_path.read_text()
start_marker = '    float placement_radius = clamp('
end_marker = '    frag_color = vec4(color, 1.0);'
start = shader.find(start_marker)
end = shader.find(end_marker)
if start < 0 or end < 0 or end <= start:
    raise SystemExit('could not locate placement controls in presentation shader')
replacement = '''    // Presentation capture: no noninteractive placement controls.\n    if (u_placement_kind == -2147483647) {\n        color = color.bgr;\n    }\n\n    frag_color = vec4(color, 1.0);'''
shader = shader[:start] + replacement + shader[end + len(end_marker):]
shader_path.write_text(shader)
PY

(
    cd android
    ./gradlew --no-daemon :app:assembleDebug
)

apk="android/app/build/outputs/apk/debug/app-debug.apk"
activity="org.isomorphisms.analyticcontinuation.lasso.dev/org.isomorphisms.analyticcontinuation.ExplorerActivity"

# Portrait physical dimensions become a 960x540 landscape surface when the
# ExplorerActivity locks to landscape. Force immersive mode before launch so the
# screen recording contains no clock/status/navigation chrome.
adb shell wm size 540x960
adb shell wm density 160
adb shell settings put secure immersive_mode_confirmations confirmed
adb shell settings put global policy_control immersive.full=*
adb install -r "$apk"
adb logcat -c
adb shell am start -W -n "$activity"
sleep 3
adb shell settings put global policy_control immersive.full=*
sleep 1

adb logcat -d > holomorphic-wanderers.log
grep -Fq 'holomorphic field started with 3 workers' holomorphic-wanderers.log
grep -Fq 'holomorphic field ready:' holomorphic-wanderers.log
grep -Fq 'zeros=3 poles=3' holomorphic-wanderers.log
grep -Fq 'holomorphic field first frame:' holomorphic-wanderers.log

read -r width height < <(
    sed -n 's/.*holomorphic field ready: surface=\([0-9][0-9]*\)x\([0-9][0-9]*\).*/\1 \2/p' holomorphic-wanderers.log | tail -1
)
test -n "$width"
test -n "$height"

adb exec-out screencap -p > holomorphic-wanderers-start.png

# Continuous runtime only. No input is injected while recording.
adb shell screenrecord --size 960x540 --bit-rate 8000000 --time-limit 22 /sdcard/holomorphic-wanderers.mp4
adb pull /sdcard/holomorphic-wanderers.mp4 holomorphic-wanderers.mp4
adb logcat -d > holomorphic-wanderers.log
adb exec-out screencap -p > holomorphic-wanderers-end.png

test -s holomorphic-wanderers.mp4
grep -Fq 'smooth divisor exchange complete: zeros=3 poles=3' holomorphic-wanderers.log
grep -Fq 'holomorphic field started with 3 workers' holomorphic-wanderers.log
! grep -Eiq 'shader compilation failed|program link failed|eglInitialize failed|could not choose GLES3 EGL config|could not create EGL surface/context|eglMakeCurrent failed|holomorphic field shader uniforms unavailable|FATAL EXCEPTION' holomorphic-wanderers.log

steps=$(sed -n 's/.*holomorphic field: workers=3 steps=\([0-9][0-9]*\).*/\1/p' holomorphic-wanderers.log | tail -1)
test -n "$steps"
test "$steps" -gt 0

printf 'captured %sx%s clean presentation runtime; holomorphic steps=%s\n' "$width" "$height" "$steps"
