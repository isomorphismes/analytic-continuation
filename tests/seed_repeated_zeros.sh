#!/usr/bin/env bash
set -euo pipefail

log_file=${1:-holomorphic-emulator.log}
coordinate_file=${2:-/tmp/cauchy-repeated-zero-cluster}

read -r width height < <(
    sed -n 's/.*Cauchy field ready: surface=\([0-9][0-9]*\)x\([0-9][0-9]*\).*/\1 \2/p' \
        "$log_file" | tail -1
)

test -n "${width:-}"
test -n "${height:-}"

min_side=$width
if (( height < width )); then
    min_side=$height
fi

pixel_radius=$((42 * min_side / 100))
initial_zero_x=$((width / 2 - 34 * pixel_radius / 100))
initial_zero_y=$((height / 2))
cluster_x=$((width / 2 - 120))
cluster_y=$((height / 2 + 80))
exclude_radius=$((22 * min_side / 100))

# Move the initial zero into the cluster, then add seven more within a few
# pixels. The resulting eight zeros model an order-eight repeated root while
# retaining separate draggable factors in the UI.
adb shell input swipe \
    "$initial_zero_x" "$initial_zero_y" \
    "$cluster_x" "$cluster_y" 450
sleep 1

for offset in \
    '2 0' \
    '-2 1' \
    '1 -2' \
    '-1 -2' \
    '3 2' \
    '-3 2' \
    '0 3'
do
    read -r dx dy <<< "$offset"
    adb shell input tap "$((cluster_x + dx))" "$((cluster_y + dy))"
done

printf '%s %s %s\n' "$cluster_x" "$cluster_y" "$exclude_radius" > "$coordinate_file"
