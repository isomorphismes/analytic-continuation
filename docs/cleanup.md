# Cleanup boundary

## Goal

Keep one coherent application:

```text
ordinary Wegert-style meromorphic plane
+ explicit zeros and poles
+ continuously varying holomorphic/nonvanishing factor
```

The function changes continuously while its explicit divisor remains under user
control.  Rendering preferences and ordinary zero/pole interaction should come
from reusable Wegert pieces rather than a second copied implementation.

The lasso/domain-warp, overlapping-disc, and path/sheet/Riemann-surface ideas
have moved to `isomorphismes/lacunary`.

## Already removed from the live direction

| Surface | Destination / reason |
| --- | --- |
| Python movie/Manim path | Retired; a desktop movie renderer is not the app. |
| Rational convergence-disc reveal | `lacunary#1`; it changes the local-domain/reveal problem. |
| Lasso / deformed-domain model | `lacunary#2`; it changes the domain coordinates and inverse-map problem. |
| Germ/path/branch/monodromy continuation | `lacunary#3`; broader chart/Riemann-surface work. |

Git history retains the old experiments; selected mathematical pieces are being
archived in Lacunary.

## Keep here

- native EGL/OpenGL ES Android shell;
- the ordinary meromorphic zero/pole picture;
- multiplicity and normal zero/pole editing through reusable Wegert components;
- canonical Wegert value -> color behavior;
- random candidate generation for nearby holomorphic motions;
- pre-step analytic sensitivity scoring / preferred-direction selection;
- mathematical validation and safe step extent;
- a compact accepted motion descriptor that the GPU can evaluate continuously;
- Android, emulator, and target-phone evidence.

A useful experimental form is

```text
f_t(z) = R(z) exp(q_t(z))
```

because `exp(q_t)` is holomorphic and nonzero wherever `q_t` is holomorphic, so
it cannot change the zero/pole divisor carried by `R`.  This is a convenient
construction, not a claim that all future holomorphic freedom must be expressed
as a polynomial exponent.

## Remaining false-start coupling

The current source still has this shape:

```text
analytic_continuation_random.c
  includes analytic_continuation.c
    owns rational factors plus old lasso/domain-warp machinery
```

The problem is the lasso/domain-warp coupling and duplicated application code,
not the existence of zeros and poles.

Replace it with explicit pieces:

1. `holomorphic_field`: proposes/scores/validates nearby holomorphic motion and
   publishes a safe descriptor;
2. `explorer_shell`: Android lifecycle, camera, pause, and input routing;
3. `wegert_adapter`: thin use of exported Wegert coloring and ordinary
   zero/pole interaction components, without copied palette/factor code.

## Extraction acceptance

The extraction is complete when:

- shipping source no longer textually includes another `.c` file;
- `lasso_map`, inverse-lasso Newton solves, lasso dragging, lasso derivative
  budgets, and moving factor-preimage state are gone from this app;
- explicit zero and pole state remains available on the ordinary complex plane;
- zero/pole UI and coloring are consumed from reusable Wegert components rather
  than maintained independently here;
- holomorphic motion is represented independently of domain warping;
- candidate directions are scored before acceptance using analytic quantities
  such as phase/log-modulus sensitivity;
- accepted movement has an explicit safe extent or equivalent validation;
- the fragment shader evaluates the accepted field at display cadence;
- pause, pan/zoom, lifecycle restart, zero/pole editing, and visible flowing
  motion have target-phone evidence.

## Do not reintroduce

- Manim/Manimi runtime or movie-viewer ownership of the app;
- lasso/domain-warp machinery here;
- convergence-disc/path/branch state here;
- copied Wegert rendering math that can drift;
- new `refC` dependencies.
