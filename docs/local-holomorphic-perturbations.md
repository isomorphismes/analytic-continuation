# Local holomorphic perturbation engine

## Goal

Start from a holomorphic function already being domain-colored and make many small random visible changes without ever leaving the holomorphic family.

Do not choose one finite-dimensional global coefficient space for the vibration. Instead, repeatedly choose a point in the visible domain and generate a small holomorphic perturbation associated with that point.

The first Android target should budget **four ARM worker threads** for generating perturbations, with three workers as an easy lower-load setting. The GPU remains responsible for evaluating the resulting field over pixels and coloring the panel.

## Fundamental constraint

A nonzero holomorphic perturbation cannot have compact support. If it vanishes on an open set, the identity theorem makes it vanish everywhere on the connected domain.

So a perturbation cannot be a true two-dimensional bump centered on a chosen pixel. It can become imperceptibly small over much of the panel, but some disturbance must escape in at least one direction.

This is useful rather than merely inconvenient: the engine can choose or derive an escape direction and stop paying for regions where the effect is below the visual threshold.

## Measure the visible change in log-polar coordinates

Let the current function be `f` and the changed function be `f_new`.

For a small additive perturbation `delta_f`,

```text
Delta log|f| + i Delta arg(f)
    = log(f_new / f)
    = log(1 + delta_f / f)
    ~= delta_f / f.
```

Thus `|delta_f / f|` is a useful first-order visibility measure away from zeros.

A threshold such as

```text
tau = 0.1
```

means that changes smaller than roughly `0.1` in the combined log-modulus / argument coordinates do not need to be drawn for the first prototype.

Single-precision float error is a much smaller threshold than this, so perceptibility should normally stop the calculation long before float resolution does.

## Diagnostic primitive: add a constant

Given a randomly selected point `a`, a requested small phase change `alpha` can be imposed exactly at that point with

```text
delta = f(a) * (exp(i alpha) - 1)
f_new(z) = f(z) + delta.
```

This remains holomorphic. For small `alpha`,

```text
|delta| ~= |f(a)| |alpha|.
```

The visible effect away from zeros is approximately

```text
|delta / f(z)|.
```

The direction in which this effect initially grows fastest is the direction in which `|f|` decreases fastest. If

```text
q = f'(a) / f(a),
```

then a unit steepest-descent direction is

```text
v = -conj(q) / |q|.
```

The corresponding continuous escape curves satisfy

```text
dz/ds = -conj(f'(z) / f(z)),
```

and along them

```text
d/ds log|f(z)| = -|f'(z) / f(z)|^2 <= 0.
```

Near a simple zero these curves point approximately toward the zero.

This primitive is valuable for tests and visualization of propagation, but it is **not** sufficient for the production vibration engine: many constant additions collapse to one net constant and therefore do not retain independent spatial identities.

## Production form: multiplicative holomorphic perturbations

Use

```text
f_new(z) = f(z) * exp(g(z))
```

where `g` is a small holomorphic function chosen by one perturbation worker.

This has several useful properties:

1. `f_new` is holomorphic whenever `f` and `g` are holomorphic.
2. Existing zeros of `f` and their multiplicities are preserved.
3. For a meromorphic `f`, existing poles are also preserved and no new zeros or poles are introduced by `exp(g)`.
4. The color-coordinate displacement is especially simple:

```text
Delta log|f| = Re(g)
Delta arg(f) = Im(g)       modulo 2 pi.
```

So `|g(z)|` directly bounds both color-coordinate changes. There is no first-order approximation in this representation; it is the exact multiplicative perturbation before argument wrapping.

To rotate the chosen point by a small angle `alpha` without changing its modulus at that point, require

```text
g(a) = i alpha.
```

The remaining mathematical problem is therefore precise:

> Given a domain, a point `a`, and a small complex value `eta`, choose a cheap canonical holomorphic `g` with `g(a) = eta` and with as little perceptible disturbance elsewhere as possible.

## Canonical candidate on a disk: minimum-L2 perturbation

On the unit disk, the Bergman kernel gives a canonical answer to the previous problem. Among square-integrable holomorphic functions with a prescribed value at `a`, the normalized kernel is the minimum-L2 choice.

Define

```text
phi_a(z) = (1 - |a|^2)^2 / (1 - conj(a) z)^2.
```

Then

```text
phi_a(a) = 1
```

and we may take

```text
g(z) = eta * phi_a(z).
```

For a pure phase nudge,

```text
eta = i alpha.
```

The magnitude is

```text
|g(z)| = |eta| (1 - |a|^2)^2 / |1 - conj(a) z|^2.
```

This makes the unavoidable escape explicit. The kernel is small over part of the disk and grows toward a boundary direction. If `a = 0`, the minimum-L2 perturbation is constant, which is exactly what rotational symmetry should force: there is no preferred escape direction from the center.

For a visibility threshold `tau`, the worker can derive the perceptible region analytically from

```text
|g(z)| >= tau.
```

For `a != 0`, this is equivalent to

```text
|1 - conj(a) z|
    <= (1 - |a|^2) sqrt(|eta| / tau).
```

The boundary is a circle whose center lies outside the unit disk; its intersection with the visible disk is the perceptible cap / escape region. This gives a cheap conservative tile bound without sampling the whole panel on the CPU.

The disk kernel is the first mathematically principled candidate, not a commitment that every visible domain must be a disk. For a rectangular or lasso-shaped domain we can later choose a different kernel, conformal map, or finite approximation.

## Preserving user constraints

Multiplication by `exp(g)` automatically preserves every zero constraint already satisfied by `f`.

If points `c_1, ..., c_m` are required to remain at value `1`, then for small perturbations we should impose

```text
g(c_k) = 0
```

for every such point.

A simple way to enforce this is to multiply the unconstrained perturbation by

```text
P_1(z) = product_k (z - c_k)
```

and renormalize at the selected point `a`:

```text
g_constrained(z)
    = eta * phi_a(z) * P_1(z)
      / (phi_a(a) * P_1(a)).
```

This is valid when `a` is not itself one of the pinned `1` points. Higher-order derivative constraints can be represented by higher multiplicities in the vanishing factor.

This construction may enlarge the perceptible region; the worker must recompute its bound rather than assuming the unconstrained kernel's bound.

## Four-worker ARM design

Use a fixed worker pool rather than creating and destroying threads.

Each worker repeatedly:

1. draws a random visible-domain point `a`;
2. draws a small signed phase or log-modulus nudge `eta`;
3. chooses the current perturbation primitive;
4. constructs a compact descriptor for `g`;
5. computes a conservative perceptibility bound / tile list using `tau`;
6. pushes the descriptor into a multi-producer queue consumed by the render thread.

The worker should normally **not** compute individual pixel colors. It computes the analytic perturbation and enough geometry to tell the GPU where evaluating it is worthwhile.

Suggested initial descriptor fields:

```text
anchor_re
anchor_im
eta_re
eta_im
born_time
lifetime
primitive_kind
bound_min_x
bound_max_x
bound_min_y
bound_max_y
```

The exact representation should remain float32 on the Android path unless a numerical test demonstrates a need for more precision.

## Damping without breaking holomorphicity

Give each perturbation a scalar time envelope `w_j(t)`, for example a smooth exponential decay after birth.

At a given frame define

```text
G(z, t) = sum_j w_j(t) g_j(z)
```

and render

```text
f_vibrating(z, t) = f_base(z) * exp(G(z, t)).
```

At every fixed time, `G` is holomorphic and therefore `f_vibrating` is holomorphic. As old weights decay to zero, the display returns toward the constrained base function rather than accumulating permanent random drift.

Independent perturbations combine by addition in `G`, which is both mathematically closed and GPU-friendly.

## GPU pass

First prototype:

1. ARM workers generate descriptors asynchronously.
2. The render thread drains a bounded batch once per frame.
3. The GPU evaluates `f_base(z)` once per pixel.
4. The shader sums active `g_j(z)` contributions.
5. It evaluates `f_base(z) * exp(sum g_j(z))` and applies the existing domain coloring.

Do the simple full-panel version first with a small bounded active perturbation count. This establishes correctness and measures the actual phone before adding a complicated sparse path.

Second prototype:

1. workers attach conservative screen-space bounds or tile lists;
2. perturbations are binned into tiles;
3. each pixel evaluates only perturbations assigned to its tile;
4. a perturbation may be dropped from a tile once its maximum possible `|g_j|` there is below the visibility budget.

Because skipped perturbations add, the culling rule must account for the **sum** of omitted bounds. It is not enough to say that every omitted perturbation is individually below `tau` if thousands of them could add coherently.

## Initial correctness tests

1. **Holomorphic closure**: compare numerical Cauchy-Riemann residuals before and after several simultaneous perturbations.
2. **Anchor value**: verify `g(a) = eta` to float32 tolerance.
3. **Zero preservation**: zeros of `f_base` remain zeros under multiplication by `exp(G)`.
4. **Pinned-one preservation**: constrained perturbations keep every pinned `f = 1` point fixed to float32 tolerance.
5. **Damping**: after all perturbation weights decay, the rendered function returns to the base function.
6. **Visibility bound**: pixels skipped by the CPU/tile bound differ by less than the configured color-coordinate tolerance.
7. **Determinism mode**: fixed random seeds reproduce the same perturbation stream for emulator and CI tests.

## First implementation slice

Keep the first code slice deliberately small:

- four long-lived ARM perturbation workers;
- deterministic per-worker RNG streams;
- multiplicative `f * exp(G)` composition;
- one cheap holomorphic primitive plus the constant-add diagnostic;
- float32 descriptors;
- fixed maximum active perturbation count;
- simple damping;
- no sparse tile culling until the full-panel path is measured on the phone.

The important invariant is stronger than a visual approximation:

> Every displayed frame should correspond to an explicitly represented holomorphic function. Perceptibility thresholds are allowed to reduce rendering work, but they must not be used to define the mathematical function itself.
