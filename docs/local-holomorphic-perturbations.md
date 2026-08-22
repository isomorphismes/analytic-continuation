# Local holomorphic perturbation engine

## Goal

Start from a holomorphic or meromorphic function already being domain-colored and make small random visible changes while every displayed frame still represents an explicitly holomorphic perturbation of that function.

Do not choose one finite-dimensional global coefficient space for the vibration. Instead, repeatedly choose points in the visible domain and generate small holomorphic perturbations associated with those points.

The first Android prototype uses **three ARM perturbation workers plus one lightweight coordinator thread**. The existing render thread remains separate. The GPU evaluates the combined perturbation over the panel and performs the domain coloring.

## Fundamental constraint

A nonzero holomorphic perturbation cannot have compact support. If it vanishes on an open set, the identity theorem makes it vanish everywhere on the connected domain.

So a perturbation cannot be a true two-dimensional bump centered on a chosen pixel. It can become imperceptibly small over much of the panel, but some disturbance must escape in at least one direction.

The engine therefore represents the perturbation globally and may later use perceptibility bounds only to avoid unnecessary evaluation work.

## Measure color displacement directly

Use a multiplicative perturbation

```text
f_new(z) = f(z) * exp(g(z))
```

with holomorphic `g`. Then

```text
Delta log|f| = Re(g)
Delta arg(f) = Im(g)       modulo 2 pi.
```

This is exact, not merely a first-order approximation. The shader therefore does not need to evaluate a complex exponential: it can add `Re(g)` directly to log modulus and `Im(g)` directly to phase before applying the existing domain coloring.

Existing zeros and their multiplicities are preserved. For meromorphic `f`, existing poles are preserved as well because `exp(g)` has neither zeros nor poles.

A visual threshold such as

```text
tau = 0.1
```

can later be used to skip regions whose total omitted `|g|` is safely below perceptibility. The mathematical function itself must remain the full holomorphic sum; the threshold is only a rendering optimization.

## First perturbation primitive: normalized Bergman kernel on a disk

On the unit disk, define

```text
phi_a(z) = (1 - |a|^2)^2 / (1 - conj(a) z)^2.
```

Then

```text
phi_a(a) = 1.
```

For a small pure phase nudge `alpha`, use

```text
g(z) = i alpha phi_a(z).
```

At the selected point `a`, this changes phase by exactly `alpha` while leaving log modulus unchanged there.

Its magnitude is

```text
|g(z)| = |alpha| (1 - |a|^2)^2 / |1 - conj(a) z|^2.
```

This gives a canonical minimum-L2 holomorphic perturbation with an explicit escape direction. At `a = 0`, rotational symmetry makes the minimum-L2 perturbation constant, so there is no distinguished escape direction.

For an arbitrary visible rectangle, the prototype places that rectangle strictly inside a containing disk and maps the randomly selected visible point into the disk. The pole of the kernel therefore remains outside the containing disk and hence outside the visible rectangle at the instant the perturbation is generated.

This containing-disk construction is a first implementation primitive, not a claim that the disk kernel is ultimately the best perturbation family for every domain.

## Three perturbation workers

There are exactly three long-lived perturbation worker threads.

Each worker owns one active perturbation slot. When the coordinator requests a replacement, the worker:

1. snapshots the current visible center, scale, and aspect ratio;
2. draws a random point in the visible rectangle;
3. draws a small signed phase amplitude;
4. constructs the containing-disk Bergman descriptor;
5. precomputes the normalized anchor and kernel scale;
6. publishes the completed descriptor into its slot;
7. sleeps until the coordinator asks for another perturbation.

The workers do not paint pixels and do not call GLES. Their output is a compact analytic description of a holomorphic function.

The first descriptor contains only float32 mathematical values:

```text
disk_center_re
disk_center_im
inverse_disk_radius
anchor_re
anchor_im
kernel_scale
phase_amplitude
```

Each worker has its own `xorshift32` random stream.

## Coordinator thread

A fourth perturbation-system thread is deliberately lightweight. It is the coordinator rather than another mathematical worker.

Roughly once per frame it:

1. checks the three worker slots;
2. computes each perturbation's scalar damping weight;
3. retires perturbations that have decayed below the recycle threshold;
4. asks the corresponding worker to generate a replacement;
5. publishes a compact snapshot containing at most three active descriptors for the render thread.

The coordinator does no per-pixel work and normally does no expensive complex analysis. It is primarily scheduling, lifetime management, and handoff.

The prototype uses exponential damping:

```text
alpha(t) = alpha_0 exp(-age / decay_time).
```

At every fixed time, multiplying a holomorphic perturbation by this real scalar leaves it holomorphic. With three active fields,

```text
G(z,t) = g_1(z,t) + g_2(z,t) + g_3(z,t)
```

and the displayed function is

```text
f_vibrating(z,t) = f_base(z) * exp(G(z,t)).
```

So simultaneous perturbations remain holomorphic by construction.

Timing is stored as integer monotonic nanoseconds. Elapsed time is converted to float32 seconds for the damping calculation. The perturbation mathematics uses floats, not doubles.

## GPU path

The render thread copies the coordinator's published snapshot once per frame and uploads at most three descriptors as GLES uniforms.

For every pixel the fragment shader:

1. evaluates the existing base function's phase and log modulus;
2. evaluates each active normalized Bergman kernel;
3. adds the real part of `i alpha phi_a(z)` to log modulus;
4. adds the imaginary part to phase;
5. applies the existing Wegert-style domain coloring.

Because

```text
i alpha (x + i y) = -alpha y + i alpha x,
```

the shader uses

```text
log_modulus -= alpha * kernel_imaginary
phase       += alpha * kernel_real
```

No complex exponential is needed in the fragment shader.

The first prototype deliberately evaluates all active perturbations across the full panel. Three kernels per pixel is small enough to establish correctness and measure the actual device before adding sparse tile machinery.

## Current numerical parameters

The initial implementation uses small values chosen for an obvious but controlled vibration:

```text
initial |alpha|:       0.055 .. 0.135 radians
decay time:            0.70 .. 1.20 seconds
recycle threshold:     |alpha| < 0.0045
coordinator cadence:   about 16 ms
active perturbations:  at most 3
```

These are tuning parameters, not mathematical commitments.

## Preserving user constraints

Multiplication by `exp(g)` automatically preserves every zero constraint already satisfied by `f`.

If points `c_1, ..., c_m` must remain at value `1`, each perturbation should additionally satisfy

```text
g(c_k) = 0.
```

One simple construction is to multiply the unconstrained perturbation by

```text
P_1(z) = product_k (z - c_k)
```

and renormalize at the selected point `a`:

```text
g_constrained(z)
    = eta * phi_a(z) * P_1(z)
      / (phi_a(a) * P_1(a)).
```

This part is **not yet wired into the Android prototype**. The current code establishes the worker/coordinator/GPU pipeline first.

## Perceptibility and later sparse evaluation

For the Bergman primitive, the region in which a single perturbation exceeds threshold `tau` can be derived analytically from

```text
|alpha| (1 - |a|^2)^2 / |1 - conj(a) z|^2 >= tau.
```

A later version can convert this into conservative screen-space tile bounds so pixels need only examine perturbations that can matter there.

Culling must bound the **sum** of all omitted perturbations. It is not sufficient for every omitted perturbation to be individually below `tau` if many omitted terms could add coherently.

Sparse culling is intentionally deferred until the full-panel three-perturbation version is measured on the phone.

## Current implementation status

The branch now contains working code for the first architecture slice:

- three long-lived native C perturbation workers;
- one native C coordinator thread;
- float32 perturbation descriptors;
- integer monotonic clocks for lifetime management;
- independent deterministic-form RNG streams seeded at startup;
- exponential damping and automatic replacement;
- a bounded three-descriptor snapshot handed to the render thread;
- GLES uniform upload glue;
- fragment-shader evaluation of the three normalized Bergman kernels;
- continuous rendering while vibration is active;
- a host C test for worker startup, descriptor validity, anchor bounds, and kernel normalization;
- CI configuration to compile and run that worker test.

Still deliberately absent:

- pinned-`1` constraint factors;
- perceptibility tile culling;
- measured device performance tuning;
- a UI control for vibration strength or on/off state;
- a policy for reseeding active kernels after very large camera moves.

The central invariant remains:

> Every displayed frame is represented as the base function times the exponential of a sum of explicitly holomorphic perturbations. Rendering optimizations may approximate what is evaluated, but they do not define the mathematical function.