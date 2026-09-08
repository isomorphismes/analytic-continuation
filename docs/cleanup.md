# Cleanup boundary

## Goal

Keep one coherent application:

```text
ordinary Wegert-style meromorphic plane
+ explicit zeros and poles
+ continuously varying holomorphic/nonvanishing factor
```

The function changes continuously while its explicit divisor remains under user control. Rendering preferences and ordinary zero/pole interaction should come from reusable Wegert pieces rather than a second copied implementation.

The lasso/domain-warp, overlapping-disc, and path/sheet/Riemann-surface ideas have moved to `isomorphismes/lacunary`.

## Removed from the live application

| Surface | Destination / reason |
| --- | --- |
| Python movie/Manim path | Retired; a desktop movie renderer is not the app. |
| Rational convergence-disc reveal | `lacunary#1`; it changes the local-domain/reveal problem. |
| Lasso / deformed-domain model | `lacunary#2`; it changes the domain coordinates and inverse-map problem. |
| Germ/path/branch/monodromy continuation | `lacunary#3`; broader chart/Riemann-surface work. |

The historical lasso map/inverse and convergence-disc planner/path geometry are archived in Lacunary with provenance. Git history here retains the full old Android experiments.

The live source no longer includes the old `analytic_continuation.c`, inverse-lasso Newton solves, lasso dragging, moving factor preimages, or a lasso launcher icon.

## Current live model

The current experimental field is

```text
f_t(z) = R(z) exp(q_t(z))
```

where `R` is the explicit zero/pole divisor on the ordinary complex plane. Because `exp(q_t)` is holomorphic and nonzero wherever `q_t` is holomorphic, it cannot change that divisor.

Three CPU workers currently propose nearby coefficient directions for `q`. Before movement, candidates are scored using exact analytic response:

```text
delta log|exp(q)| = Re(delta q)
delta phase(exp(q)) = Im(delta q)
```

The render thread chooses the lowest-scoring fresh direction and advances only while the explicit coefficient budget remains satisfied. The shader evaluates the resulting field everywhere and then calls the canonical Wegert value-to-color core.

This is a useful prototype, not the final scheduling architecture. The GPU-native target remains a compact accepted motion segment/descriptor that can be interpolated at display cadence while search and validation run more slowly.

## Remaining integration debt

The Lacunary extraction is complete, but the ordinary meromorphic editor is still partly app-local. The next cleanup is narrower:

1. keep the holomorphic field/search code here;
2. keep the Android lifecycle/camera/pause shell here;
3. consume reusable Wegert zero/pole state, dragging/placement, coordinate mapping, and rendering pieces through a thin adapter rather than maintaining parallel behavior.

The canonical `wegert_color.glsl` boundary is already enforced byte-for-byte in CI. Extend that ownership discipline to the ordinary zero/pole interaction without moving zeros/poles out of this application.

## Acceptance for the next extraction

- explicit zero and pole state remains available on the ordinary complex plane;
- zero/pole multiplicity and normal editing come from reusable Wegert components;
- no lasso/domain-warp or continuation-path state returns here;
- holomorphic motion remains independent of domain warping;
- candidate directions are scored before acceptance using analytic quantities such as phase/log-modulus sensitivity;
- accepted movement has an explicit safe extent or equivalent validation;
- the fragment shader evaluates the accepted field at display cadence;
- pause, pan/zoom, lifecycle restart, zero/pole editing, and visible flowing motion have target-phone evidence.

## Do not reintroduce

- Manim/Manimi runtime or movie-viewer ownership of the app;
- lasso/domain-warp machinery here;
- convergence-disc/path/branch state here;
- copied Wegert rendering or interaction math that can drift;
- new `refC` dependencies.
