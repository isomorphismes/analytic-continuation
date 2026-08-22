# `analytic-continuation/movie-v1`

The movie file is a strict JSON object. Unknown fields are errors. Existing
files that omit `view.mode` keep the default whole-plane behavior.

## Top level

| field | required | meaning |
| --- | --- | --- |
| `schema` | no | Must be `analytic-continuation/movie-v1` when present. |
| `function` | yes | One explicit registry function and its parameters. |
| `view` | no | Camera, grid, and reveal mode. |
| `animation` | no | Open, hold, close, sampling, and clipping settings. |
| `probes` | no | Complex input points whose outputs are computed by the function. |
| `title` | no | Nonempty movie title. |

Complex values are finite JSON numbers, `[real, imag]` pairs, or objects with
`real` and optional `imag` fields. `Infinity`, `NaN`, and expression strings
are not complex values in this contract. A finite input mapped to infinity is
represented by the selected function's pole metadata (or by a rational pole
factor), not as a nonfinite JSON number.

## Rational factors

```json
"function": {
  "name": "rational",
  "parameters": {
    "gain": [1, 0],
    "zeros": [[-1, 0], [2, 0]],
    "poles": [[0, 0]]
  }
}
```

This means

```text
f(z) = gain × product(z - zero) / product(z - pole).
```

Each repeated location is another factor and therefore increases its
multiplicity. Exact matching zero and pole factors cancel one-for-one before
evaluation, metadata, labels, markers, and continuation radii are built. For
example, one zero at `1` and two poles at `1` leave one pole at `1`; a zero at
`1.000001` remains distinct. Gain must be nonzero. The canonical finite factor
lists plus nonzero gain describe the complete rational model, not merely a few
constraints on an otherwise unspecified analytic function.

## View

The defaults are:

```json
"view": {
  "center": [0, 0],
  "half_height": 4,
  "grid_step": 1,
  "mode": "whole"
}
```

`half_height` and `grid_step` must be positive finite real numbers. In `whole`
mode, a `disc_reveal` object is rejected so that ignored settings cannot look
effective.

Disc-reveal mode is explicit:

```json
"view": {
  "mode": "disc_reveal",
  "disc_reveal": {
    "path": [[2, 0], [2, 1], [1, 2]],
    "patch_reveal_seconds": 0.35
  }
}
```

- `path` is a required nonempty list of finite complex disc centers.
- `patch_reveal_seconds` is a required positive finite real number.
- The radius at each center is its distance to the nearest completely known
  finite pole. It is infinite for an entire function.
- Each center after the first must lie strictly inside the preceding open disc.
- A center cannot be a pole.
- Functions are rejected when their finite singularity list is incomplete or
  branch tracking would be needed.

The renderer reveals these checked patches in path order, then evaluates the
registered closed form for the usual open/close deformation. `disc_reveal` is
not analytic continuation: it does not calculate Taylor coefficients, carry a
germ, or propagate values from patch to patch. The name `continuation` remains
available for that later operation. Patches clip the exact whole-view plane
lattice, including axes and faded subdivisions; their overlapping line
intervals are merged into a geometric union before the deformation.

## Animation

`animation` accepts `open_seconds`, `hold_seconds`, `close_seconds`, `close`,
`curve_density`, and `output_margin`. Times are nonnegative finite real
numbers. `curve_density` is an integer from 8 through 500. `output_margin` is
positive and at most 1.
