from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageStat


MIN_MEAN_ABS_RGB = 1.5
MIN_CHANGED_FRACTION = 0.10
PIXEL_CHANGE_THRESHOLD = 8


def measure_motion(first_path: Path, second_path: Path) -> tuple[float, float]:
    first = Image.open(first_path).convert("RGB")
    second = Image.open(second_path).convert("RGB")
    if first.size != second.size:
        raise SystemExit("motion screenshots have different dimensions")

    width, height = first.size
    box = (
        int(width * 0.10),
        int(height * 0.15),
        int(width * 0.90),
        int(height * 0.85),
    )
    diff = ImageChops.difference(first.crop(box), second.crop(box))
    mean_abs_rgb = sum(ImageStat.Stat(diff).mean) / 3.0
    pixels = list(diff.getdata())
    changed = sum(1 for pixel in pixels if max(pixel) >= PIXEL_CHANGE_THRESHOLD)
    changed_fraction = changed / max(len(pixels), 1)
    return mean_abs_rgb, changed_fraction


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: check_cauchy_motion.py FIRST.png SECOND.png")

    mean_abs_rgb, changed_fraction = measure_motion(
        Path(sys.argv[1]), Path(sys.argv[2])
    )
    print(
        f"Cauchy motion mean_abs_rgb={mean_abs_rgb:.3f} "
        f"changed_fraction={changed_fraction:.3f}"
    )
    if (
        mean_abs_rgb < MIN_MEAN_ABS_RGB
        or changed_fraction < MIN_CHANGED_FRACTION
    ):
        raise SystemExit("Cauchy-field motion is still too visually weak")


if __name__ == "__main__":
    main()
