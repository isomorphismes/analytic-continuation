# Random holomorphic field

The live Wegert-style meromorphic portrait moves because the function changes, not because the palette or hue is animated.

The displayed function is

```text
f_t(z) = R(z) exp(q_t(z))
```

where `R` carries the explicit zeros and poles on the ordinary complex plane and

```text
q(u) = c1 u + c2 u^2 + ... + c5 u^5,
u = z / 6
```

is the current experimental holomorphic field. Because `exp(q)` is entire and nonzero, changing `q` cannot create, remove, or move the zeros and poles supplied by `R`.

## Candidate directions

Exactly three pthread workers are retained for the current CPU search prototype. Each keeps a heading, samples 128 nearby/random normalized coefficient directions, and scores the candidate **before** the render state advances.

For a coefficient direction `d`,

```text
delta q(u) = d1 u + d2 u^2 + ... + d5 u^5.
```

The exact infinitesimal response of the nonvanishing factor is

```text
delta log|exp(q)| = Re(delta q)
delta phase(exp(q)) = Im(delta q).
```

The present score samples those two analytic sensitivities over a fixed set of points, plus a smaller derivative term. Near the coefficient-budget boundary, outward directions receive an extra penalty. This is a concrete first direction preference, not a claim that it is canonical.

The render thread takes the lowest-scoring fresh result, smoothly steers its coefficient velocity toward that direction, and accepts a candidate step only while the explicit coefficient budget remains satisfied. Search snapshots are published more slowly than display frames; the GPU evaluates the accepted coefficients over every fragment.

## Rendering boundary

The shader computes the meromorphic zero/pole contribution and `q(z)`, adds `Re(q)` to log modulus and `Im(q)` to phase, then hands those values to the canonical Wegert coloring core. Interaction overlays are drawn after that value-to-color boundary.

Pause stops coefficient motion. Zeros and poles can be added or dragged directly in the visible `z` plane. Lasso/domain-warp and overlapping-disc experiments are not part of this implementation; they live in `isomorphismes/lacunary`.
