# Random holomorphic deformation

This branch makes the live Wegert-style rational portrait move because the function changes, not because the hue phase walks.

The deformation coordinate is the existing holomorphic map

```text
h(w) = w + a2 w^2 + a3 w^3 + ... + a6 w^6.
```

The displayed rational map is composed with the local inverse of `h`.  When the coefficients move, stored zero and pole preimages are recomputed so their positions in the visible `z` plane stay fixed.  A tap adds a zero; pole placement is not part of this slice.

## GPU-wide flowing experiment

Issue #33 replaces the three-worker search in the live build with one compact
descriptor evaluated by every fragment:

```text
q_t(w) = a_1(t) w + a_2(t) w^2
F_t(w) = F_0(w) exp(q_t(w)).
```

The CPU publishes only elapsed animation time.  The two complex coefficients
follow fixed bounded circles, and the fragment shader evaluates `q_t` and its
analytic derivative

```text
q_t'(w) = a_1(t) + 2 a_2(t) w.
```

Because `q_t` is entire and its exponential is entire and nonzero, this
experiment adds no zeros and no poles.  The zeros and poles of the displayed
rational map therefore remain exactly the explicitly stored factors.  The
shader applies the exponential without constructing it: `Re(q_t)` is added to
log-modulus and `Im(q_t)` to phase, avoiding overflow and preserving the exact
domain-coloring meaning.

There is no screen-space finite difference, pixel feedback, histogram, Gram
matrix, dominant-direction search, compute pass, or CPU reduction.  This slice
tests the architecture and the visible effect, not optimal variation.

## Retired three-worker experiment

Exactly three pthread workers search coefficient-space directions.  Each worker keeps a heading, samples 128 nearby/random normalized holomorphic perturbations, and scores their infinitesimal disturbance on a fixed set of points in the unit disc.

For a coefficient direction `d`, the infinitesimal deformation is

```text
δh(w) = d2 w^2 + d3 w^3 + ... + d6 w^6.
```

The score is a sampled mean of `|δh|^2` plus a smaller `|δh'|^2` term.  Near the existing derivative-budget boundary, directions that increase that budget receive an additional penalty.  This is a concrete first definition of "least holomorphic disturbance", not a claim that it is canonical.

The render thread takes the lowest-scoring fresh result from the three workers, smoothly steers its coefficient velocity toward that direction, and advances the coefficients.  Every proposed step still passes the existing univalence/derivative-budget and zero/pole-preimage checks.  Rejected steps bounce the velocity inward and immediately request a new search.

The old random hue-phase walk is bypassed in this player.  Pause stops coefficient motion.  Manual lasso deformation and factor dragging temporarily take ownership and the random walk resumes afterward.
