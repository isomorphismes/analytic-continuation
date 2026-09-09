#!/usr/bin/env bash
set -euo pipefail

# The first attempt drove the markers with separate adb swipe commands, which made
# the video visibly stop/start. For this capture, make the actual app own the
# trajectories. The holomorphic soup keeps advancing in the normal app loop while
# the divisor positions are updated every frame.
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

    /* Let the soup establish itself, then wander continuously for 16 seconds. */
    float raw = (float)((now - engine->wander_start_time - 5.0) / 16.0);
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
PY

# Rebuild after injecting the smooth in-app wanderer. This is still the actual
# holomorphic application derived from the holomorphic tag; there are no generated
# frames, no interpolation and no adb-driven marker jumps in the recording.
(
    cd android
    ./gradlew --no-daemon :app:assembleDebug
)

apk="android/app/build/outputs/apk/debug/app-debug.apk"
activity="org.isomorphisms.analyticcontinuation.lasso.dev/org.isomorphisms.analyticcontinuation.ExplorerActivity"

adb shell wm size 720x1280
adb shell wm density 320
adb install -r "$apk"
adb shell settings put secure immersive_mode_confirmations confirmed
adb logcat -c
adb shell am start -W -n "$activity"
sleep 3

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

# Nothing drives the markers from adb. The app updates all six trajectories at
# its normal animation cadence while the holomorphic field evolves independently.
adb shell screenrecord --bit-rate 10000000 --time-limit 23 /sdcard/holomorphic-wanderers.mp4
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

printf 'captured %sx%s smooth runtime video; holomorphic steps=%s\n' "$width" "$height" "$steps"
