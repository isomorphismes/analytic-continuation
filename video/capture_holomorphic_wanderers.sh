#!/usr/bin/env bash
set -euo pipefail

apk="android/app/build/outputs/apk/debug/app-debug.apk"
activity="org.isomorphisms.analyticcontinuation.lasso.dev/org.isomorphisms.analyticcontinuation.ExplorerActivity"

adb shell wm size 720x1280
adb shell wm density 320
adb install -r "$apk"
adb shell settings put secure immersive_mode_confirmations confirmed
adb logcat -c
adb shell am start -W -n "$activity"
sleep 4

adb logcat -d > holomorphic-wanderers.log
grep -Fq 'holomorphic field started with 3 workers' holomorphic-wanderers.log
grep -Fq 'holomorphic field ready:' holomorphic-wanderers.log
grep -Fq 'zeros=1 poles=1' holomorphic-wanderers.log
grep -Fq 'holomorphic field first frame:' holomorphic-wanderers.log

read -r width height < <(
    sed -n 's/.*holomorphic field ready: surface=\([0-9][0-9]*\)x\([0-9][0-9]*\).*/\1 \2/p' holomorphic-wanderers.log | tail -1
)
test -n "$width"
test -n "$height"

min_side="$width"
if (( height < width )); then
    min_side="$height"
fi
scale=$((42 * min_side / 100))
cx=$((width / 2))
cy=$((height / 2))

# The tagged explorer starts with a zero at (-0.34, 0) and a pole at (+0.34, 0).
# Move them on opposite broad arcs so each keeps its type while they exchange places.
left_x=$((cx - 34 * scale / 100))
right_x=$((cx + 34 * scale / 100))
upper_y=$((cy - 28 * scale / 100))
lower_y=$((cy + 28 * scale / 100))
upper_left_x=$((cx - 16 * scale / 100))
upper_right_x=$((cx + 16 * scale / 100))
lower_left_x=$((cx - 16 * scale / 100))
lower_right_x=$((cx + 16 * scale / 100))

adb exec-out screencap -p > holomorphic-wanderers-start.png

adb shell screenrecord --bit-rate 8000000 --time-limit 20 /sdcard/holomorphic-wanderers.mp4 > /tmp/holomorphic-screenrecord.log 2>&1 &
record_pid=$!
sleep 2

# Zero: left -> high left -> high right -> original pole territory.
adb shell input swipe "$left_x" "$cy" "$upper_left_x" "$upper_y" 1500
sleep 1
# Pole: right -> low right -> low left -> original zero territory.
adb shell input swipe "$right_x" "$cy" "$lower_right_x" "$lower_y" 1500
sleep 1
adb shell input swipe "$upper_left_x" "$upper_y" "$upper_right_x" "$upper_y" 1700
sleep 1
adb shell input swipe "$lower_right_x" "$lower_y" "$lower_left_x" "$lower_y" 1700
sleep 1
adb shell input swipe "$upper_right_x" "$upper_y" "$right_x" "$cy" 1500
sleep 1
adb shell input swipe "$lower_left_x" "$lower_y" "$left_x" "$cy" 1500
sleep 2

wait "$record_pid" || true
adb pull /sdcard/holomorphic-wanderers.mp4 holomorphic-wanderers.mp4
adb logcat -d > holomorphic-wanderers.log
adb exec-out screencap -p > holomorphic-wanderers-end.png

test -s holomorphic-wanderers.mp4
grep -Fq 'holomorphic field started with 3 workers' holomorphic-wanderers.log
! grep -Eiq 'shader compilation failed|program link failed|eglInitialize failed|could not choose GLES3 EGL config|could not create EGL surface/context|eglMakeCurrent failed|holomorphic field shader uniforms unavailable|FATAL EXCEPTION' holomorphic-wanderers.log

# Confirm the soup kept advancing while the divisor was being dragged.
steps=$(sed -n 's/.*holomorphic field: workers=3 steps=\([0-9][0-9]*\).*/\1/p' holomorphic-wanderers.log | tail -1)
test -n "$steps"
test "$steps" -gt 0

printf 'captured %sx%s runtime video; holomorphic steps=%s\n' "$width" "$height" "$steps"
