# Analytic Continuation

Native Android explorer for a meromorphic complex function whose holomorphic
freedom stays alive.

The intended picture is the ordinary Wegert-style complex plane with explicit
zeros and poles, multiplied by a continuously varying holomorphic/nonvanishing
factor:

```text
f_t(z) = R(z) H_t(z)
```

`R` carries the visible meromorphic divisor.  `H_t` moves through legitimate
holomorphic states without introducing accidental zeros or poles.  One useful
experimental family is

```text
H_t(z) = exp(q_t(z))
```

but the repository should not confuse one convenient family with a complete
parameterization of holomorphic functions.

The motion changes the mathematical function, not merely the hue.

## Direction search

Randomness proposes nearby holomorphic motions.  Before a step is taken, the
explorer should use analytic information to score candidate directions and
validate a safe extent.  For an `exp(q)` family,

```text
delta log|H(z)| = Re(delta q(z))
delta phase(H(z)) = Im(delta q(z))
```

so phase/log-modulus sensitivity can guide a preferred direction without using
RGB finite differences as mathematics.

The search/validation side may publish a compact safe segment or perturbation
descriptor at a slower cadence while the fragment shader evaluates the accepted
motion continuously at display cadence.

## Wegert boundary

[Wegert](https://github.com/isomorphismes/wegert) owns reusable phase-portrait
behavior and rendering preferences, including the canonical complex-value to
Wegert-color mapping and ordinary zero/pole interaction pieces.

This repository should consume those pieces rather than copy them.  Its own
responsibility is the evolving holomorphic factor, candidate-direction search,
mathematical validation, GPU evaluation, and thin Android integration.

The current Android implementation still contains inherited lasso/domain-warp
machinery inside `analytic_continuation.c`.  That is migration debt, not the
architecture.  See issue #25 and [`docs/cleanup.md`](docs/cleanup.md).

## Lacunary boundary

[Lacunary](https://github.com/isomorphismes/lacunary) owns the experiments that
change the domain/chart/continuation problem rather than simply changing the
holomorphic factor on the ordinary meromorphic plane:

- lasso and deformed-domain constructions;
- overlapping convergence discs and reveal geometry;
- path-dependent germ transport;
- branches, sheets, monodromy, and broader Riemann-surface experiments.

Those experiments remain valuable, but they no longer define this app.

## Runtime

The Android project is under `android/`.  It uses a C `NativeActivity`, EGL, and
OpenGL ES 3.  No Python runtime or desktop movie renderer owns the live
interaction.

Current host checks include the holomorphic direction-search code and Wegert
color-parity boundary.  Android build/emulator receipts and target-phone GPU
receipts remain separate evidence.

## Historical work

Old movie, convergence-disc, lasso, completion, and perturbation experiments
remain in Git history.  Lasso/disc/path material is being archived or rehomed in
Lacunary.  Random-holomorphic experiments can still be useful here when they
advance the live field architecture without reintroducing domain-warp or chart
machinery.
