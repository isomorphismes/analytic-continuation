# Rigidity and famous-function recognition

The central experience should make two different kinds of rigidity visible:

1. a declared mathematical law plus a few editable pieces can determine one
   holomorphic germ;
2. once that germ exists, agreement on open overlaps forces its analytic
   continuation through a connected region.

The first step gives the player a small number of things to move. The second
step shows why all the unedited values move with them. The interface must name
which theorem supplies each claimed uniqueness.

## The relevant smoothness

`C^∞` smoothness is not rigid enough. A smooth map from the plane to itself can
be altered inside a small region without changing it elsewhere.

`C^ω` ordinarily means real-analytic. That is stronger, but it still does not
by itself mean holomorphic: complex conjugation is real-analytic and not
complex-differentiable.

The application therefore uses **holomorphic on an open domain** as its core
condition. A holomorphic function is automatically complex-differentiable of
every order, `C^∞`, and real-analytic. It is conformal only at points where its
derivative is nonzero, so `conformal` is not a synonym for `holomorphic`.

If two holomorphic functions on a connected domain agree on a set with a limit
point in that domain, the identity theorem says that they agree everywhere.
Analytic continuation applies this uniqueness to a germ carried through a
chain of overlapping open regions. Existence is not automatic. Continuation
along a fixed path is unique when it exists, while different paths can lead to
different branches.

## What a few pieces can and cannot force

A circle is determined by three non-collinear points because the allowed
objects have already been restricted to circles. Holomorphicity alone does not
make a finite set of values determine a function. If `p(zⱼ) = wⱼ`, then every function

```text
p(z) + h(z) × product(z - zⱼ)
```

has the same sampled values for every entire `h`.

Every rigidity story must therefore declare four things:

- the domain;
- the admissible function family or law;
- the independently editable pieces;
- the named functions that can be recognized inside that family.

A function is **forced** only when exactly one admissible function satisfies
the snapped constraints. The display must also name the reason, such as
`three-point Möbius uniqueness`, `bounded-degree interpolation`, `ODE
uniqueness`, or `identity theorem`.

Finite zeros and poles do not determine an arbitrary meromorphic function on
the plane: multiplication by a nonvanishing factor such as `exp(h(z))`
preserves them. The Wegert factor input is determining only when it declares a
complete rational model on the Riemann sphere: every zero and pole with its
multiplicity, together with a nonzero gain.

## Interaction

### Determine a germ

The initial view exposes the law and its editable pieces. As pieces snap into
place, the application recomputes which named functions the law still permits.
Consequences forced by the law change everywhere at once; they are not counted
as additional user changes.

The first lessons should be finite models whose uniqueness is easy to state:

| lesson | editable pieces | source of uniqueness | useful named targets |
| --- | --- | --- | --- |
| Möbius maps of the sphere | images of an ordered triple of distinct points, kept distinct | three point correspondences determine one Möbius map | identity, `1 - z`, `1 / z`, Cayley transform |
| polynomials of degree at most `n` | values at `n + 1` distinct points | bounded-degree interpolation | line, parabola, selected cubics |
| `f″ + f = 0` | `f(0)` and `f′(0)` | uniqueness for a second-order ODE | sine and cosine |
| `f″ = zf` | `f(0)` and `f′(0)` | uniqueness for the Airy equation | Airy Ai and Airy Bi |
| rational maps of the sphere | all zero and pole factors plus gain | complete divisor plus normalization | simple Möbius and bounded rational maps |

Möbius maps are the closest direct analogue of three points determining a
circle. Sine and cosine give the clearest two-piece transition between famous
functions: the law stays visible while the two initial values move.

Zeta, gamma, Airy, or Bessel must not be recognized merely because a few
sampled values or zeros resemble them. They require a declared law, canonical
parameters, or an already established germ.

### Continue the germ

Once a germ has been determined, the player moves an overlapping disc along a
path. The overlap must have an open region; discs that merely touch do not
supply identity-theorem evidence. The old and new expansions agree visibly on
the overlap, after which the newly forced region appears.

The first genuine continuation story should start with the geometric-series
germ and reach `1 / (1 - z)`. This makes it clear that two formulas describe
one function on their common domain. A logarithm story can later show branch
tracking and monodromy.

The existing `disc_reveal` view is only a closed-form preview of pole-free disc
geometry. It must never report that continuation occurred. A future
`continuation` operation must carry Taylor data from one center to the next and
make the overlap agreement inspectable.

## Famous-function catalog

Each named entry needs:

- one stable canonical identity;
- one or more display names and equivalent formulas;
- its domain and, when necessary, a chosen branch or germ;
- a canonical inspectable mathematical model;
- its independently editable pieces;
- a theorem-backed exact recognizer;
- a stable teaching order for otherwise tied results.

Equivalent names for the same function belong on one card. They are not two
competing candidates. An undecidable or unsupported identity returns
`unknown`; sampled agreement never upgrades it to exact equality.

The current evaluator stores callables. Recognition will also need to retain
canonical data such as polynomial coefficients, rational gain and factors,
and Bessel order rather than trying to recover them from a closure.

## `almost` and `near`

These words describe reachability through declared mathematical changes, not
pixel resemblance.

Let `rigidity_change` mean one legal change to one independently manipulable
piece. The finite edit graph then gives:

- exact: shortest change count `0`;
- `almost`: shortest change count exactly `1`;
- `near 3`: shortest change count at most `3`.

The relation `near 3` includes exact and `almost` mathematically. The user
interface presents disjoint bands: exact for `0`, `almost` for `1`, and `near`
for `2` or `3`.

The Idriç surface words should remain general proof-bearing relations:

```text
almost relation left right
near change_limit relation left right
```

This application specializes `relation` to `rigidity_change`; the language
must not bake this editor or the default limit of three into the words. A
witness for either relation contains a shortest legal change path to an exact
named target.

One change means one independent mathematical piece:

- moving one complex zero changes both coordinates but counts once;
- adding, removing, or relocating one declared factor counts once;
- changing one initial value counts once;
- forced global consequences count zero times;
- pan, zoom, probe motion, label placement, factor reordering, and equivalent
  symbolic rewrites count zero times;
- replacing the whole expression is never one change;
- a no-op cannot witness `almost`.

Pointer proximity should use names such as `within_hit_radius` and
`within_snap_radius`. Numerical approximation should use `within_error`.
Snapping may use floating-point distance, but a successful snap stores the
intended symbolic value. Only the symbolic or theorem-backed state enters an
`almost`, `near`, or exact proof.

## Name display

The display shows at most two distinct famous functions in total. Normally one
card keeps the chosen source visible and the other shows the closest target. If
there is no named source, or the source is no longer pedagogically relevant,
both slots may show targets. Candidates are ordered by:

1. shortest change count;
2. explicit teaching order;
3. stable canonical identity.

Each target card shows its name, the band `exact`, `almost`, or `near`, and the
change path or uniqueness reason. If more candidates tie at the cutoff, the
display says how many more exist instead of pretending that the functions
shown are mathematically closer. The source is deduplicated if it is also a
current candidate.

Visual hysteresis may prevent cards from flickering during a drag, but it does
not alter the recognized mathematical state.

## Implementation boundary

The general function movie generator remains independent. The rational
zero-pole work supplies canonical factor data and `disc_reveal`; it does not
become the rigidity engine.

The next implementation needs separate responsibilities for:

- canonical inspectable function models;
- the famous-function catalog;
- exact and shortest-path recognition;
- germs, overlaps, and continuation witnesses;
- rendering the stable source card and at most two target cards.

The actual continuation story belongs above camera `view.mode`: it coordinates
a law, editable pieces, a germ, a path, recognition, and explanatory text.
Reserving `almost` and `near` in Idriç belongs on its own Idriç branch; this
repository supplies the concrete proof obligations that those general
relations must support.

## Required tests

- finite samples without a declared finite model do not recognize a famous
  function;
- aliases canonicalize to one exact target;
- `almost` contains a minimal one-change witness;
- `near 3` contains a minimal path of at most three changes;
- camera and probe changes do not affect recognition;
- ranking is deterministic and returns no more than two displayed targets;
- a snapped value is stored symbolically before exact recognition;
- the first continuation story propagates a germ rather than resampling its
  known closed form;
- `disc_reveal` never claims an analytic-continuation witness.
