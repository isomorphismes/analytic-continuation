# Ithon zero and infinity placement

This is the first interactive slice. New interaction logic is written in
Ithon (`.pi`), not Python. The older Python movie renderer remains temporary
reference material while the Manimi Ithon rewrite acquires its rendering and
Android boundaries.

The screen initially has two placement choices: **zero** and **∞**. A selected
choice persists. A finger-down on empty mathematical space begins a possible
placement. Releasing within 12 pixels of that finger-down places the selected
kind at the release position. Moving farther than 12 pixels does not place
anything; that gesture remains available for later panning.

The coordinate conversion is copied from Wegert:

- screen `x` increases to the right;
- screen `y` increases downward, so it is reversed for the imaginary axis;
- `half_height` sets the imaginary range;
- the real range also uses the screen aspect ratio;
- camera center is added after conversion;
- placement does not snap to a grid.

Repeated placements are retained because they may later represent
multiplicity. An infinity placement stores a finite input position where the
function is intended to take the value ∞; it does not try to store infinity as
a complex coordinate.

This slice deliberately omits hit-testing existing placements, dragging,
panning, zooming, function evaluation, and continuation. Wegert's rule for the
later extension remains: choose any existing target once at finger-down and do
not retarget during the drag.
