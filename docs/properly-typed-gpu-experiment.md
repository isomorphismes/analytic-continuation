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

The first compiler exercise used `isomorphisms/idris-shader-backend` commit `4360f29d3bbdc09b4cc513e4a6be647f290ffede` (`complex-projective/follower`). Later structural probes overlay that complex arithmetic follower onto the generic and Mali control-flow branches so the same typed source can be compared directly.

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

## Why the first typed APK was slow

The first generated fragment flattened every `active_factor_measure` into eager arithmetic followed by a select. As a result, a scene with one zero and one pole still evaluated all 32 zero slots and all 32 pole slots for every pixel. The generated fragment contained 64 `atan` calls and 64 `log` calls outside real control flow.

The handwritten fragment does not have this behavior: its loops stop once the uniform zero or pole count is reached. The tablet's greater-than-one-second visible response to a touch therefore exposed a compiler control-flow problem rather than an intended interaction delay.

## Structural backend fix

The generic shader backend now has a `fix/structured-control-flow` branch, and the Mali-G57 branch has the same large-fragment recovery incorporated into `opt/mali-g57-fp16-precision`.

For each typed select, the recovery pass follows both result dependency chains, separates shared from branch-exclusive work, finds values required outside the branch, protects the complete dependency closure of those values, and moves only the remaining closed branch-local subgraph. Expensive pure work becomes real GLSL `if`/`else` control flow. The earlier Mali prototype's 256-binding global cutoff is no longer used.

The exact current Analytic Continuation typed core has 1,159 IR lines. Cross-repository run `34311467111` compiled it through both improved backends in both highp and lowp modes. All four generated shaders validated as GLSL ES.

| compiler | precision | shader lines | `atan` | gated `atan` | `log` | gated `log` | real `if` | ternary selects |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| generic structured | highp | 1,395 | 64 | 64 | 64 | 64 | 68 | 0 |
| generic structured | lowp | 1,395 | 64 | 64 | 64 | 64 | 68 | 0 |
| Mali structured | highp | 1,395 | 64 | 64 | 64 | 64 | 68 | 0 |
| Mali structured | lowp | 1,395 | 64 | 64 | 64 | 64 | 68 | 0 |

This means inactive factor slots no longer execute their `atan`/`log` chains. The highp and lowp variants have the same recovered control-flow structure.

This remains compiler/GLSL validation evidence. Physical Mali-G57 timing must still be measured with an APK built from the improved fragment.

## Precision provenance

The high precision used in the earlier experiment was inherited rather than required by the mathematical design. The handwritten Analytic Continuation fragment explicitly declared `precision highp float;`, and the generic backend also historically emitted highp for its current F32 semantic path by default.

For the `properly-typed` experiment the handwritten fragment now explicitly declares `precision lowp float;`. Both improved shader backends also accept an explicit `float-precision=lowp` emission directive. The backend keeps GLSL precision class separate from mathematical/type semantics: lowp is an intentional rendering choice here, not a redefinition of the complex or real number types.

Physical PowerVR acceptance remains separate from the Mali tablet test and also remains open.
