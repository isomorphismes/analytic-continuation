# Holomorphic

Native Android explorer for a meromorphic complex portrait with explicit zeros and poles plus a continuously moving holomorphic field.

The visible picture is

```text
f_t(z) = R(z) H_t(z)
H_t(z) = exp(q_t(z))
```

`R` carries the user-visible meromorphic divisor. On the experimental `cauchy-field` branch,

```text
q_t(z) = sum_k a_k / (xi_k(t) - z)
```

with every source `xi_k(t)` kept outside a disk containing the complete visible viewport. Consequently `q_t` is holomorphic throughout the visible region and `H_t` is nonzero there. The circles remain zeros and the X marks remain the explicit poles contributed by `R`.

This is deliberately a visible-region construction, not an entire-function construction. Globally, each `q_t` has poles at its off-screen Cauchy sources and `exp(q_t)` has essential singularities there. The branch therefore changes the whole-plane contract rather than pretending that an off-screen singularity is harmless mathematically.

## GPU Cauchy field

The live deformation is evaluated per fragment. The CPU does not search polynomial coefficient directions or maintain a coefficient budget. It supplies elapsed time plus the ordinary interaction state; the fragment shader synthesizes the moving source positions and evaluates the same time-dependent field at every pixel.

The experiment uses 24 Cauchy sources. Their trajectories now use the smooth orbital geometry promoted on `main`: deterministic starting directions, slow clockwise or counterclockwise orbital motion, smooth radial bending, and slight ellipticity. The source scale is still viewport-relative, with

```text
base = 1.8 * view_radius
radial bend <= 0.35 * view_radius
```

and ellipticity bounded by 8%. Even at the inward extreme the Euclidean source distance is at least `0.92 * 1.45 = 1.334 * view_radius`, so every Cauchy singularity remains outside the visible disk.

The complex source weights are deterministic and fixed in time. Visible evolution therefore comes from the orbiting source geometry rather than an independent rotation of the residues.

For

```text
f(z) = R(z) exp(q(z))
```

the shader uses the exact decomposition

```text
log|f(z)| = log|R(z)| + Re(q(z))
phase(f(z)) = phase(R(z)) + Im(q(z))
```

and sends those completed values to the canonical Wegert color core. No explicit complex exponential is required.

## Interaction

The native explorer retains ordinary zero and pole placement, factor dragging, and pinch zoom. The current experimental zoom range is `0.1` through `32.0`.

The Cauchy source field is viewport-relative: changing the viewport radius also relocates the hidden source orbits so that the sources remain outside the visible region. Zoom is therefore not mathematically independent of this experimental deformation field.

## Wegert boundary

[Wegert](https://github.com/isomorphismes/wegert) owns reusable phase-portrait behavior and rendering preferences, including the canonical complex-value-to-Wegert-color mapping and ordinary zero/pole interaction pieces.

This repository consumes Wegert's exported coloring core and checks it byte-for-byte against Wegert in CI. Its own responsibility is the evolving holomorphic factor, mathematical evolution, GPU evaluation, and thin Android integration.

The inherited lasso/domain-warp engine has been removed from the live source. The remaining integration cleanup is to replace the app-local ordinary zero/pole interaction code with reusable Wegert components without changing the meromorphic playground itself; see issue #25 and [`docs/cleanup.md`](docs/cleanup.md).

## Lacunary boundary

[Lacunary](https://github.com/isomorphismes/lacunary) owns experiments that change the domain/chart/continuation problem rather than simply changing the field on the ordinary visible plane:

- lasso and deformed-domain constructions;
- overlapping convergence discs and reveal geometry;
- path-dependent germ transport;
- branches, sheets, monodromy, and broader Riemann-surface experiments.

Reusable historical mathematics from those experiments has been archived there. Git history here still records the old branches, but none of that machinery is part of the shipping explorer.

## Runtime and acceptance

The Android project is under `android/`. It uses a C `NativeActivity`, EGL, and OpenGL ES 3. No Python runtime or desktop movie renderer owns the live interaction.

The retired CPU holomorphic walk, its worker threads, sample-point direction search, polynomial coefficient uniforms, and coefficient budget are absent from the active Cauchy-field build. Acceptance checks the GPU/time-uniform architecture, the Wegert color boundary, absence of migrated lasso machinery, native APK construction, runtime zero/pole interaction, and live frame-to-frame motion from the running APK. The APK and emulator screenshots are uploaded as build artifacts so the experiment can be judged from actual execution rather than CI status alone.

The whole-plane entire model remains a legitimate alternative, but it is not the semantics of this branch.
