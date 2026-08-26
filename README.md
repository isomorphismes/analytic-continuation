# Analytic continuation

The released application is a native Android explorer for domain coloring,
zeros, poles, and convergence-disc geometry. It launches directly into a C
`NativeActivity` with an EGL/OpenGL ES 3 renderer and touch loop adapted from
Wegert. No desktop animation engine or Python runtime is packaged in the app.

The repository also keeps a small renderer-independent Python reference model.
It validates strict JSON fixtures, evaluates a named function registry, and
checks the distinction between revealing pole-free discs and actually carrying
a germ along a path. It does not render video.

## Reference model

- choose a named complex function in JSON;
- set the visible complex domain;
- use the default `whole` view or describe a path with `disc_reveal`;
- optionally record input probes;
- validate finite drawing coordinates and continuation-disc geometry without
  binding those contracts to a renderer.

The registry currently contains:

| input name | function | status in the complex variable |
| --- | --- | --- |
| `exp` | exponential | entire |
| `sin` | sine | entire |
| `polynomial` | coefficients in ascending powers | entire |
| `rational` | nonzero gain, zeros, and poles | meromorphic |
| `zeta` | Riemann zeta | meromorphic continuation; one pole at `1` |
| `gamma` | gamma | meromorphic |
| `airy_ai`, `airy_bi` | Airy functions | entire |
| `bessel_j` | Bessel J with an order parameter | entire for integer order; branched at `0` otherwise |

There is no Python `eval` input. A new function gets an explicit registry
entry and parameter contract.

## Check it

Python 3.10 or later is required.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .

analytic-continuation list-functions
analytic-continuation validate examples/zeta.json
analytic-continuation validate examples/rational_disc_reveal.json
```

The examples include zeta, Airy Ai, Bessel J order zero, and rational maps
exported from Wegert.

Run the small non-rendering test suite with:

```sh
python -m unittest discover -s tests -v
```

## Native Android explorer

The live model is the normalized rational function

```text
g(z) = product(z - zero) / product(z - infinity-point).
```

The initial non-polynomial example is `g(z) = (z + 1) / (z - 1)`. Tap ○ or ∞
and then the portrait to edit its factors. Exact opposite factors cancel
one-for-one. In convergence-disc view, the radius at each center is the
distance to the nearest uncancelled finite point mapped to ∞, and a new center
must lie strictly inside the preceding open disc. Revealed discs show the live
phase portrait; everything else is a function-independent charcoal weave, so
hidden values do not leak through the background.

This explorer visualizes valid convergence-disc geometry while evaluating the
selected function directly. It does not yet propagate Taylor coefficients or
track branches. The Play workflow builds an installable debug APK for
validation and a signed native AAB. See
[`docs/google-play-release.md`](docs/google-play-release.md).

Direct test installs use an update-stable, test-only GitHub APK that launches
the live native explorer without video playback. See
[`docs/github-apk-release.md`](docs/github-apk-release.md).

## Retained visualization JSON

The original `analytic-continuation/movie-v1` schema remains as
renderer-independent compatibility data. The complete strict contract is
documented in [`docs/movie-v1.md`](docs/movie-v1.md). A future guided-rendering
path must enter through checked Manimi/Ithon source; the retired renderer is not
a fallback.

Complex values are JSON numbers, `[real, imag]` pairs, or objects with `real`
and `imag` fields.  They are never expression strings.

```json
{
  "schema": "analytic-continuation/movie-v1",
  "title": "Bessel J₀(z)",
  "function": {
    "name": "bessel_j",
    "parameters": {"order": 0}
  },
  "view": {
    "center": [0, 0],
    "half_height": 6,
    "grid_step": 1
  },
  "probes": [[0, 0], [2.4048255577, 0]],
  "animation": {
    "open_seconds": 5,
    "hold_seconds": 1,
    "close_seconds": 5,
    "close": true,
    "curve_density": 80,
    "output_margin": 0.94
  }
}
```

### Disc-reveal view

The default `view.mode` is `whole`, so existing specification files remain valid. A
`disc_reveal` view supplies a nonempty path of Taylor-disc centers and an
explicit reveal time for each patch:

```json
"view": {
  "center": [0, 0],
  "half_height": 3.2,
  "grid_step": 0.5,
  "mode": "disc_reveal",
  "disc_reveal": {
    "path": [[2, 0], [2, 1], [1, 2], [0, 2]],
    "patch_reveal_seconds": 0.35
  }
}
```

For a function whose finite singularities are completely known, each disc
extends from its center to the nearest pole.  Entire functions have no finite
radius bound.  Every next center must lie strictly inside the preceding disc.
Functions with incomplete finite-singularity metadata, or functions requiring
branch tracking, are rejected rather than shown misleadingly.

This mode previews pole-free disc geometry.  It is **not analytic
continuation**: it does not carry a germ or calculate a new Taylor expansion.
It checks and reveals the overlapping discs in path order, then evaluates the
selected closed form to map the grid. Overlapping line intervals are merged so
the same grid segment is not represented twice. The name `continuation`
remains free for a later mode that actually propagates a germ and demonstrates
uniqueness.

## Wegert boundary

Wegert already has the right input for rational maps.  Its zeros and poles,
together with one nonzero complex gain, determine

```text
f(z) = gain × product(z - zero) / product(z - pole).
```

`examples/wegert_rational.json` is the proposed export shape.  The Wegert
camera maps directly to `view.center` and `view.half_height`.  Tapped portrait
locations can be exported as `probes`; their output values are determined by
the selected function.

Repeated zero or pole locations represent multiplicity and are retained in
the function metadata.  Exact matching zero and pole factors cancel
one-for-one before evaluation, labels, markers, or Taylor radii are
built.  Nearby but unequal locations remain distinct, so a raw transient
Wegert state is safe to export.  `examples/rational_disc_reveal.json` places
two zeros and one pole, then previews a valid loop of overlapping discs around
that pole.
The loop starts at one of the zeros, which is a regular Taylor-disc center.

A few freely chosen input/output pixel pairs do **not** determine an analytic
function.  Infinitely many polynomials, and still more analytic functions,
can pass through any finite set.  If the user is constructing a function,
the UI must also choose a model such as a rational degree, a differential
equation with initial data, or a Taylor germ.

## Later: computing continuation rather than visualizing its geometry

The intended rigidity interaction, famous-function cards, and proof-bearing
meanings of `almost` and `near` are specified in
[`docs/rigidity.md`](docs/rigidity.md).

A continuation computation needs more data than the current disc view:

1. a base point and a Taylor germ (or an equation that determines one),
2. a path through the complex plane,
3. overlapping convergence discs avoiding singularities,
4. branch tracking when different paths produce different values.

That mode can reveal the continued Wegert portrait one disc at a time.  It is
especially useful for `log`, `sqrt`, non-integer Bessel functions, and other
multivalued functions.  Airy Ai/Bi and integer-order Bessel J are already
entire, so their whole-plane visualizations are complex-map deformations, not
dramatic examples of continuation across a barrier.
