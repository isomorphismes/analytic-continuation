# Properly typed GPU probe

This directory is the first compiler-backed experiment on the existing handwritten Analytic Continuation fragment.

`Example/AnalyticContinuationHandwrittenCore.idr` re-expresses the mathematical/color core of `android/app/src/main/assets/continuation.frag.in` without changing the live Android renderer. It preserves the current fragment's important shapes and constants:

- 32 zero slots;
- 32 pole slots;
- five complex coefficients for `q(z)`;
- the current `z / 3` normalization;
- the current `1e-16` squared-radius floor;
- `Re(q)` added to log modulus and `Im(q)` added to phase;
- the current Wegert phase/log-modulus to HCL/sRGB mapping.

The first probe deliberately leaves the zero/pole markers and placement buttons in handwritten GLSL. They are interaction overlays, not the complex-function field being tested here.

The `properly-typed-gpu` workflow checks out the complex/projective shader-backend follower at an exact commit, builds its compiler backend, compiles this typed twin to GLSL ES 3.00 plus typed IR, validates and links the generated fragment, and separately validates the live handwritten fragment assembled with the canonical Wegert core.

A passing compiler/link receipt is not a physical-GPU receipt. Driver shader loading, GPU execution, framebuffer comparison, and phone evidence remain explicit later gates.
