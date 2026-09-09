# Mumford note: test structure, not pixel churn

This note exists because the Cauchy-field acceptance test found a real failure in our
notion of motion.

With one simple zero/pole configuration, raw screenshot difference looked like a
reasonable proxy for a moving field. With eight nearly coincident zeros, the image
could accumulate enormous RGB change while the large visible forms appeared much
less mobile. A test reporting "92% of pixels changed" was therefore answering the
wrong question.

The reference to return to is:

- David Mumford and Agnes Desolneux, *Pattern Theory: The Stochastic Analysis of
  Real-World Signals* (A K Peters/CRC Press, 2010), especially the image chapters on
  cartoon/texture separation, texture statistics, deformation, and multiscale
  analysis.

## Working distinction

Do not conflate these three claims:

1. **The mathematical field moves.**
   Test the Cauchy contribution `q_t(z)` directly, before roots, poles, or coloring.
2. **The rendered pixels change.**
   Screenshot RGB difference can remain a useful smoke test.
3. **Large-scale rendered structure moves.**
   This needs a geometric, multiscale test. It is the property a person means when
   saying that the "soup" visibly wanders or morphs.

The first two do not imply the third.

## Mumford-inspired direction

Treat an image as containing coarse/geometric organization plus finer oscillatory
texture. Repeated roots can make the fine phase/color texture churn without causing
an equally strong displacement of coarse structure.

For future acceptance work:

- mask the immediate neighborhoods of zeros and poles when they would dominate a
  measurement;
- construct a Gaussian pyramid (for example 1, 1/2, 1/4, 1/8, 1/16 resolution);
- emphasize gradients or other palette-insensitive coarse structure rather than raw
  RGB at the coarser levels;
- divide coarse levels into reasonably large blocks and find where each block's
  structure moved between two real APK frames;
- measure displacement magnitude, spatial coherence between neighboring blocks, and
  how much a smooth geometric warp of frame A improves its match to frame B;
- require meaningful motion at more than one scale so that neither a single moving
  edge nor high-frequency recoloring can satisfy the test by itself.

A minimal first implementation should prefer deterministic block matching over a
large optical-flow or machine-learning dependency. The test should remain inspectable:
we should be able to say which coarse regions moved, by how far, and whether neighboring
regions moved coherently.

## What not to do

- Do not turn up the Cauchy amplitudes merely to make an RGB threshold pass.
- Do not use percent-changed-pixels as the definition of visible motion.
- Do not substitute a single Fourier/power-spectrum difference for geometry; texture
  statistics and spatial organization are different questions.
- Do not fake motion from screenshots. Renderer/video evidence must still come from
  the running app/APK.
- Do not delete the direct `q_t` test. It cleanly proves that the off-screen wanderers
  themselves are moving even when the divisor hides or transforms their visual effect.

## Current acceptance target

Keep three independent gates:

- **field-motion gate**: direct change of `q_t` on sampled visible points;
- **pixel-motion gate**: coarse smoke test that the running APK is not frozen;
- **structure-motion gate**: multiscale coherent displacement of coarse image
  organization.

The third gate is the missing one. When designing it, go back to Mumford/Desolneux
rather than inventing another whole-frame scalar that can be fooled by texture churn.

## First calibrated structure-motion test

The first implemented structural gate is `tests/check_cauchy_structure_motion.py`.
It is deliberately simpler than full block matching or optical flow. It compares the
raw RGB motion with the motion that survives aggressive grayscale low-pass/downsample
steps at several coarse scales. The useful quantity is the fraction of raw motion
retained after fine color texture has been suppressed.

Current acceptance threshold:

- median coarse-motion retention must be at least `0.30`.

Calibration came from real running-APK captures, not synthetic images:

| case | raw RGB mean change | coarse grayscale change | retention | result |
| --- | ---: | --- | --- | --- |
| ordinary one-zero/one-pole soup | `2.822` | `[1.536, 1.467, 1.446]` | `[0.544, 0.520, 0.512]`, median `0.520` | PASS |
| eight nearly coincident zeros | `32.197` | `[6.444, 6.015, 5.644]` | `[0.200, 0.187, 0.175]`, median `0.187` | FAIL |

The repeated-root frame pair still passed the old pixel-motion gate with about `92.6%`
of eligible pixels changing, yet failed the structural gate. That is exactly the
failure mode this note was meant to capture: **more pixel churn can coexist with less
large-scale motion**.

The ordinary APK rerun passed the new structural gate at `0.520`, giving useful
separation around the `0.30` threshold. An earlier ordinary six-second window failed
the old RGB gate (`mean_abs_rgb=1.152`, `changed_fraction=0.032`) before reaching the
structural checker, while a rerun passed (`2.822`, `0.186`). Treat that as evidence
that a single fixed RGB window is a brittle smoke test; do not weaken the structural
threshold to accommodate it. A later improvement can sample several time windows.

This first structural test is an oracle for current renderer work, not the end of the
Mumford direction. The next stronger version should estimate coarse block displacement,
neighbor coherence, and warp improvement so that it measures actual geometric motion
rather than only survival under scale-space filtering.

## Papers actually consulted for this work

Keep this section distinct from a generic bibliography. These are papers or manuscripts
consulted while developing the structure-motion idea and its source trail. The Brown
copies are preferred because they are freely readable from Mumford's own archive.

- David Mumford and Jayant Shah, **"Optimal Approximations by Piecewise Smooth
  Functions and Associated Variational Problems,"** *Communications on Pure and
  Applied Mathematics* 42 (1989), 577-685.
  https://www.dam.brown.edu/people/mumford/vision/papers/1989c--Mumford-Shah-Wiley.pdf
  Relevance here: coarse piecewise structure, edges, and the idea that an image can
  have meaningful organization at a scale even when fine texture violates the model.

- David Mumford, **"Mathematical Theories of Shape: Do They Model Perception?"**
  SPIE *Geometric Methods in Computer Vision* 1570 (1991), 2-10.
  https://www.dam.brown.edu/people/mumford/vision/papers/1991d--MathThShape-DAM.pdf
  Relevance here: explicit multiscale analysis of visual signals and the problem of
  defining similarity in terms of shape rather than raw samples.

- David Mumford, **"Pattern Theory: A Unifying Perspective,"** first European
  Congress of Mathematics (1994), revised in *Perception as Bayesian Inference*
  (1996), 25-62.
  https://www.dam.brown.edu/people/mumford/vision/papers/1994c-96--PattThUnifyingPersp-NC.pdf
  Relevance here: natural variation as domain warping/deformation and pattern models
  whose geometry is not captured by simple Gaussian or pointwise distances.

- Song Chun Zhu and David Mumford, **"Learning Generic Prior Models for Visual
  Computation,"** CVPR (1997), 463-469.
  https://www.dam.brown.edu/people/mumford/vision/papers/1997a--LearningPriors-Zhu-IEEE.pdf
  Relevance here: learn image statistics across scales rather than assume an arbitrary
  smoothness model; scale invariance is treated as a property a useful prior should
  respect.

- Song Chun Zhu and David Mumford, **"Prior Learning and Gibbs Reaction-Diffusion,"**
  *IEEE Transactions on Pattern Analysis and Machine Intelligence* 19(11) (1997),
  1236-1250.
  https://www.dam.brown.edu/people/mumford/vision/papers/1997b--PriorLGibbsR-D-Zhu-IEEE.pdf
  Relevance here: connects learned natural-image statistics, scale behavior, and
  image-processing dynamics.

- Song Chun Zhu, Yingnian Wu, and David Mumford, **"Filters, Random Fields and
  Maximum Entropy (FRAME): Towards a Unified Theory for Texture Modeling,"**
  *International Journal of Computer Vision* 27 (1998).
  https://www.dam.brown.edu/people/mumford/vision/papers/1998b--Frame-ZhuWu-journal.pdf
  Relevance here: texture can be characterized through distributions of filter
  responses; texture statistics are useful but are not the same thing as large-scale
  geometric motion.

- Jinggang Huang and David Mumford, **"Statistics of Natural Images and Models,"**
  CVPR (1999), 541-547.
  https://www.dam.brown.edu/people/mumford/vision/papers/1999c--ImageStats-Huang-IEEE.pdf
  Relevance here: direct empirical evidence for multiscale/near-scale-invariant image
  statistics and Haar/wavelet response distributions. This is a strong source for
  testing at several resolutions rather than only at native pixels.

- David Mumford, **"Pattern Theory: The Mathematics of Perception,"** ICM 2002.
  https://www.dam.brown.edu/ptg/REPORTS/02-10.pdf
  Relevance here: concise mathematical statement of pattern theory as inference over
  noisy, incomplete signals whose interesting structure repeats with variations and
  clutter.

- Ann B. Lee, Kim S. Pedersen, and David Mumford, **"The Nonlinear Statistics of
  High-Contrast Patches in Natural Images,"** *International Journal of Computer
  Vision* 54 (2003), 83-103.
  https://www.dam.brown.edu/people/mumford/vision/papers/2003a--Stats-ALeePedersen-journal.pdf
  Relevance here: local high-contrast patches concentrate near nonlinear low-dimensional
  geometric structures; full local distributions contain information that marginal or
  spectral summaries discard.

- David Mumford, **"Empirical Statistics and Stochastic Models for Visual Signals,"**
  in *Brain and Systems: New Directions in Statistical Signal Processing* (2006).
  https://www.dam.brown.edu/people/mumford/vision/papers/2006d--SurveyStochModels-PrfShts.pdf
  Relevance here: the broad survey tying together natural-image statistics, filters,
  wavelets, local primitives, scale, and stochastic image models. This is the first
  supporting paper to revisit when the current test needs a stronger statistical basis.

### Mumford archive indexes

These are useful discovery pages, not substitutes for citing the individual papers:

- image statistics: https://www.dam.brown.edu/people/mumford/vision/stats.html
- pattern theory: https://www.dam.brown.edu/people/mumford/vision/pattern.html
- shape: https://www.dam.brown.edu/people/mumford/vision/shape.html
- segmentation/parsing: https://www.dam.brown.edu/people/mumford/vision/segment.html

When adding future sources, say whether they were actually consulted for a test or are
only candidates for later reading. Do not inflate the source trail by listing every
reference in Mumford's papers.