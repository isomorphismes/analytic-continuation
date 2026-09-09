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
