# Random holomorphic deformation

This branch makes the live Wegert-style rational portrait move because the function changes, not because the hue phase walks.

The deformation coordinate is the existing holomorphic map

```text
h(w) = w + a2 w^2 + a3 w^3 + ... + a6 w^6.
```

The displayed rational map is composed with the local inverse of `h`.  When the coefficients move, stored zero and pole preimages are recomputed so their positions in the visible `z` plane stay fixed.  A tap adds a zero; pole placement is not part of this slice.

## Three workers

Exactly three pthread workers search coefficient-space directions.  Each worker keeps a heading, samples 128 nearby/random normalized holomorphic perturbations, and scores their infinitesimal disturbance on a fixed set of points in the unit disc.

For a coefficient direction `d`, the infinitesimal deformation is

```text
δh(w) = d2 w^2 + d3 w^3 + ... + d6 w^6.
```

The score is a sampled mean of `|δh|^2` plus a smaller `|δh'|^2` term.  Near the existing derivative-budget boundary, directions that increase that budget receive an additional penalty.  This is a concrete first definition of "least holomorphic disturbance", not a claim that it is canonical.

The render thread takes the lowest-scoring fresh result from the three workers, smoothly steers its coefficient velocity toward that direction, and advances the coefficients.  Every proposed step still passes the existing univalence/derivative-budget and zero/pole-preimage checks.  Rejected steps bounce the velocity inward and immediately request a new search.

The old random hue-phase walk is bypassed in this player.  Pause stops coefficient motion.  Manual lasso deformation and factor dragging temporarily take ownership and the random walk resumes afterward.
