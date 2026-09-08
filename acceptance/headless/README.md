# Deterministic complex reference scene

This directory fixes one small application-owned scene for direct x86-64,
Thumb, and shader implementations to evaluate. It defines the mathematical
input and the boundary presented to Wegert coloring. It does not implement
complex arithmetic for any backend.

The scene is deliberately independent of the random direction workers,
Android, EGL, and interaction timing. A backend can therefore produce the same
field on a thin Debian system or in GitHub Actions without a window system.

## Fixed scene

[`complex-reference-scene.json`](complex-reference-scene.json) contains only
IEEE-754 binary32 inputs, written as their exact `0x12345678` bit patterns.
The hexadecimal spelling is bit order, not host byte order. Generated program
output is explicitly little-endian.

The viewport is 96 by 64 pixel-center samples over

```text
-3 <= Re(z) <= 3
-2 <= Im(z) <= 2
```

Rows run from the largest imaginary coordinate to the smallest. The factors
are:

```text
Re(z[x,y]) = (2*x - 95) / 32
Im(z[x,y]) = (63 - 2*y) / 32
```

These are exact dyadic binary32 coordinates; no backend-dependent division by
the image width is needed.

| Kind | Position | Multiplicity |
| --- | --- | ---: |
| zero | `-0.75 + 0.25i` | 1 |
| zero | `0.625 - 0.5i` | 2 |
| pole | `-0.25 - 0.875i` | 1 |
| pole | `1.125 + 0.75i` | 1 |

No factor lies on a pixel center. Exact factor positions are instead exercised
as projective probes, where a color is not required.

Both fixed states use

```text
q_t(u) = c1 u + c2 u^2 + c3 u^3 + c4 u^4 + c5 u^5
u = z / 6
```

The `still` state has all coefficients zero. The `deformed` state uses:

```text
c1 =  0.25     + 0.125i
c2 = -0.125    + 0.1875i
c3 =  0.0625   - 0.09375i
c4 = -0.03125  + 0.046875i
c5 =  0.015625 + 0.015625i
```

Their sum of magnitudes is approximately `0.695963`, within the current `0.72`
coefficient envelope. The omitted constant term retains the live `q(0) = 0`
gauge. Every coefficient is exactly representable as binary32.

## CP1 codomain

The input grid remains in the ordinary affine complex plane. At each finite
input `z`, the function value is carried as

```text
[Q(z) : N_t(z)]

Q(z)   = product_b (z - b)^multiplicity
N_t(z) = product_a (z - a)^multiplicity * exp(q_t(z)).
```

This follows the affine convention `f -> [1:f]`, so the finite chart is
`N_t/Q`. A zero is `[Q:0]`; a pole is `[0:N_t]`, the point at infinity.

The `times-two-i` representative multiplies both coordinates by `2i`. It has a
nontrivial phase and must produce the same projective point and phase/log field
as `identity`. Backends compare projective values by a cross product, not raw
component equality.

An unreduced common zero/pole can produce `[0:0]` at its shared position. The
v1 boundary therefore rejects common factors before evaluation and rejects any
all-zero homogeneous result. A later editor integration may cancel matching
multiplicities before reaching this boundary; silently accepting `[0:0]` is not
an alternative.

This does not assert that the live function is meromorphic at the *domain*
point at infinity. For nonconstant polynomial `q`, `exp(q)` has an essential
singularity there. CP1 is used here as the codomain of values at finite affine
inputs.

## Direct-runner boundary

The backend driver consumes the scene JSON at generation time and chooses one
state and one representative. The emitted direct ELF need not contain a JSON
parser or accept command-line arguments. One execution writes exactly one
versioned stream to standard output.

The v1 stream begins with this fixed 160-byte little-endian header:

| Offset | Bytes | Meaning |
| ---: | ---: | --- |
| 0 | 8 | ASCII `ACPHF32` followed by NUL |
| 8 | 4 | unsigned version, `1` |
| 12 | 4 | header size, `160` |
| 16 | 4 | width, `96` |
| 20 | 4 | height, `64` |
| 24 | 4 | zero-based state index |
| 28 | 4 | zero-based representative index |
| 32 | 4 | bytes per sample, `8` |
| 36 | 4 | flags, zero in v1 |
| 40 | 32 | SHA-256 of the exact scene JSON bytes |
| 72 | 32 | NUL-terminated, zero-padded scene ID |
| 104 | 24 | NUL-terminated, zero-padded state ID |
| 128 | 24 | NUL-terminated, zero-padded representative ID |
| 152 | 8 | reserved zero bytes |

The payload immediately follows. It has `width * height` row-major records,
each two little-endian binary32 values:

```text
phase, log_magnitude
```

`phase` is the principal argument of `N_t/Q`; `log_magnitude` is
`log|N_t| - log|Q|`. All payload values must be finite because the fixed grid
avoids exact divisor positions. Interaction overlays are absent.

This phase/log field is the stronger mathematical receipt. The application can
turn a verified field into a dependency-free P6 PPM by applying the
digest-locked Wegert phase/log to HCL to sRGB contract. A PPM does not replace
the raw field or arithmetic receipts.

The application-side checker validates the closed scene, exact provenance,
framing, dimensions, IDs, payload length, and finite samples:

```sh
python -m acceptance.headless.reference_scene \
  validate-scene acceptance/headless/complex-reference-scene.json \
  --repository-root .

python -m acceptance.headless.reference_scene \
  verify-output acceptance/headless/complex-reference-scene.json \
  deformed identity /path/to/field.bin \
  --repository-root .

python -m acceptance.headless.reference_scene \
  render-ppm acceptance/headless/complex-reference-scene.json \
  deformed identity /path/to/field.bin /path/to/scene.ppm \
  --repository-root .
```

`render-ppm` performs the complete ACPHF32 provenance and payload validation
before opening its output. The image is exactly:

```text
ASCII "P6\\n<width> <height>\\n255\\n"
then three RGB bytes per sample in the field's row-major order
```

For each already-sRGB channel `c`, the byte conversion is
`floor(255 * clamp(c, 0, 1) + 0.5)`: nearest integer, with an exact half rounded
toward 255. No alpha byte, metadata, extra whitespace, platform newline, or
interaction overlay is emitted. Consequently, byte-identical phase/log fields
produce byte-identical PPMs even when their valid ACPHF32 headers name different
homogeneous representatives.

The host color implementation is an observational rendering adapter. It
mirrors the digest-locked GLSL formulas in binary64 and is checked against the
existing color fixture, but it neither performs nor defines generated complex
arithmetic. Shader floating-point behavior is still accepted at its separately
declared precision.

The checker deliberately does not invent a numerical tolerance for backend
transcendentals. The shared complex corpus and each implementation's declared
Float32 error contract must supply those bounds. Cross-backend comparison
should compare phase circularly and log magnitude directly before comparing
Wegert pixels, whose periodic bands have discontinuities.

## Ownership

- Analytic Continuation owns this scene, `R exp(q)` composition, CP1 value
  convention, pixel sampling, and the Wegert color-contract reference.
- The canonical Idriç mathematical layer owns Complex and projective semantics.
- The direct x86 repository owns generated arithmetic and ELF emission.
- Thumb and shader implementations follow the same scene and shared corpus.
- Wegert owns the referenced phase/log-to-color behavior.

No lasso map, deformed domain, convergence-disc planner, path state, or
Riemann-surface machinery participates in this acceptance path.
