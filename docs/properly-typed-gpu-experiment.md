# Properly typed GPU fragment experiment

This branch tests the existing handwritten Analytic Continuation fragment by re-expressing its mathematical/color core through the typed shader backend before attempting to replace the whole fragment.

## Scope

The typed source preserves the live fragment's current mathematical interface:

- 32 zero slots;
- 32 pole slots;
- five complex coefficients for `q(z)`;
- the `z / 3` normalization;
- the `1e-16` divisor radius floor;
- zero/pole phase and logarithmic-modulus accumulation;
- `Re(q)` added to logarithmic modulus and `Im(q)` added to phase;
- the canonical Wegert phase/log-modulus to RGB mapping.

The interaction marks and placement controls remain handwritten in this experiment.

The backend is pinned to `isomorphisms/idris-shader-backend` commit `4360f29d3bbdc09b4cc513e4a6be647f290ffede` (`complex-projective/follower`).

## Compiler receipt

The first compiler-only pass generated typed IR and GLSL ES 3.00 from `gpu/Example/AnalyticContinuationHandwrittenCore.idr`, validated and linked the generated fragment, and independently validated the assembled live handwritten fragment.

## Android execution receipt

The Android comparison build used the app's ordinary `NativeActivity` + EGL + GLES3 renderer. It built three APKs from source build `e7faefa8cba484e1a3ec5f2e54f8593f5e3e25cd`:

- a frozen handwritten-core probe;
- a frozen compiler-generated-core probe;
- a live compiler-generated-core probe driven by the ordinary holomorphic coefficient workers.

The packaged `assets/continuation.frag` was byte-compared against the expected handwritten or generated probe before runtime.

On the Android 34 x86-64 emulator using Google SwiftShader GLES3:

- handwritten shader load/program link: PASS;
- compiler-generated shader load/program link: PASS;
- compiler-generated GPU execution: PASS;
- frozen framebuffer comparison: PASS;
  - mean absolute RGB difference: `0.0000`;
  - fraction of pixels with channel difference >= 8: `0.000000`;
  - maximum channel difference: `1`;
- live coefficient advancement: PASS (`steps 1 -> 15` over the observed interval);
- live framebuffer response to those coefficient changes: observed, but weak;
  - mean absolute RGB difference: `0.044`;
  - about 9.55% of the central comparison pixels changed by at least one channel value;
  - the pre-existing strong visual-motion gate (`mean >= 1.5`, `>=10%` pixels changing by at least 8) did not pass in that run.

The failed strong-motion gate is not a compiler/render-equivalence failure: the frozen handwritten and compiler-generated fields matched to at most one 8-bit channel value, and the live generated shader loaded, rendered, and responded while the coefficient workers advanced. It is retained as a separate motion-quality result rather than being converted into a false GPU acceptance claim.

## Mali-G57 backend probe

The tablet-specific Mali optimization branch was tested against this exact large typed fragment using shader-backend commit `a855d89ab0f25025d825afdc194f492e4c00ecff`. The complex arithmetic follower from `4360f29d3bbdc09b4cc513e4a6be647f290ffede` was overlaid without otherwise changing the Mali compiler so that the same source could be compared directly.

The same source was compiled three ways: generic highp, Mali highp, and Mali mediump. All three generated shaders validated as GLSL ES.

The measured output was:

| compiler | precision | shader bytes | shader lines | IR lines | `atan` | `log` | real `if` | ternary selects |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| generic follower | highp | 49,749 | 1,053 | 1,159 | 64 | 64 | 0 | 68 |
| Mali optimization branch | highp | 49,749 | 1,053 | 1,159 | 64 | 64 | 0 | 68 |
| Mali optimization branch | mediump | 49,751 | 1,053 | 1,159 | 64 | 64 | 0 | 68 |

For this workload the Mali highp output is therefore structurally identical to the generic output. Its structured expensive-branch optimization does not reach the current fragment, so all 32 zero slots and 32 pole slots retain their eager `atan`/`log` work. The only observed effect of the mediump build is the requested global precision declaration; it does not repair the control-flow problem.

This is consistent with the Mali branch's deliberate current structure-analysis limit of 256 linear bindings. This fragment is much larger. The correct follow-up is not to raise that limit mechanically: the backend needs scalable use/liveness analysis or preservation of structured source control flow so inactive factors can skip their expensive work.

Physical Mali-G57 execution of an actually improved generated fragment remains the useful next device test. Physical PowerVR-device acceptance is separate and also remains open.
