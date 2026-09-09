# Agent instructions

## Rendering work is runtime work

When a task asks for a screenshot, image, video, MP4, GIF, screen recording, animation, or other visual demonstration of this app or renderer, the evidence must come from the actual software under test running.

For a tagged release, install and launch the APK built from that exact tag. For development work, identify the exact commit/build being run. A successful build, unit test, shader compile, fixture render, or standalone rendering experiment is useful evidence, but it is not a substitute for running the requested app path.

Do not substitute any of the following while claiming they show app behavior:

- AI-generated images or animation frames;
- Python, ffmpeg, HTML/canvas, desktop, or other separately implemented renderers;
- a test harness that merely resembles the app;
- cross-fades between screenshots or keyframes;
- interpolation, optical-flow synthesis, pan/zoom, stabilization, or other invented motion;
- a hand-made reconstruction of the intended visualization;
- frames produced by a different executable or renderer than the one named in the task.

If the requested behavior is not present in the current app, change the app, build a new artifact, run that artifact, and capture the resulting runtime behavior. Do not manufacture missing behavior in post-production.

## Exact backend provenance

Running an APK is necessary but is not by itself proof that the requested implementation path ran.

If a task names a compiler or rendering backend, the visual evidence counts for that backend only when the executed artifact actually contains and selects code produced by that backend. This applies in particular to `idris-shader-backend`, `idric-arm-thumb`, DEX/ART, x86-64, and any GPU-specific path.

Do not claim a backend passed merely because related source files exist in the APK or repository. Prove the path that executed. In particular:

- handwritten NDK/Clang C is not evidence for an Idriç CPU backend;
- handwritten GLSL is not evidence for `idris-shader-backend`;
- a CPU fallback is not GPU-backend evidence;
- an emulator using SwiftShader is not physical PowerVR evidence;
- successful shader compilation without a live draw is not rendering evidence;
- successful installation without proving the selected runtime path is not backend acceptance.

When fallback paths exist, make the selected path observable in logs or another runtime receipt. If the requested path cannot be proved, report it as unverified rather than silently substituting another path.

Keep enough provenance to reproduce visual evidence:

- repository and commit/tag;
- APK/build artifact and, when practical, its SHA-256;
- compiler/backend revision used to generate executable or shader code;
- device/emulator and GPU/renderer identity;
- package/process identity while recording;
- launch procedure;
- runtime evidence of backend selection and fallback status;
- raw capture or an unambiguous path to it when practical.

## Motion continuity is an acceptance requirement

A video can come from the real app and still be wrong. Inspect the runtime motion itself.

Use one continuous running process for a continuous demonstration. Do not hide resets, unrelated runs, state reloads, or discontinuities with editing.

Animation and random deformation must evolve persistent state. Do not independently redraw object positions, identities, coefficients, camera state, or deformation parameters on each frame. Randomness may drive a continuous process, but the visible state should be integrated continuously through time.

Time-step handling must tolerate ordinary frame-time variation. A dropped or delayed frame must not produce an unintended teleport or a large unrelated state update.

If an algorithm scores candidate directions, sample points, or proposed updates and then applies a different blended or larger increment, the applied motion must itself be validated or continuously interpolated. Sparse candidate scoring does not certify an arbitrary intervening step.

Before calling a moving render acceptable, inspect enough consecutive frames to catch:

- teleporting or sudden jumps;
- periodic resets or rerandomization;
- marker identities swapping accidentally;
- camera/viewport jumps not requested by the user;
- animation that freezes while only overlays move;
- background evolution that stops while poles/zeros continue moving;
- discontinuities introduced only when recording starts or loops.

If the runtime is jumpy, fix the runtime. Do not smooth, interpolate, cross-fade, or conceal the jump in the delivered video.

## Preserve the established visual language

Do not change the color pipeline merely to make motion more obvious.

Unless the task explicitly asks for a color-design change, preserve the established domain-coloring behavior, including hue, saturation, brightness/value, gamma, contrast, and any canonical Wegert color mapping or fixtures. Do not turn up saturation, exposure, contrast, or brightness as an incidental rendering change.

A mathematical change to the displayed function may naturally change the colors. But for the same function, viewport, settings, and time/state, a backend change should reproduce the same intended image within the numerical precision expected of that backend.

For renderer/backend work, keep at least one stable reference state or fixture and compare it before and after the change. Treat unexplained global hue, saturation, brightness, contrast, orientation, or viewport drift as a regression until explained.

## Mathematical identity during motion

When the visualization contains poles and zeros/holes, movement is not a type change. A pole remains a pole and a zero/hole remains a zero/hole unless the mathematical model is explicitly being changed.

Poles and zeros may wander long distances, cross paths, and exchange regions while retaining their identities. Their visible trajectories should be continuous when wandering is requested; do not accomplish an exchange by deleting and respawning differently typed markers.

When the model deliberately multiplies a rational zero/pole factor by a holomorphic nonzero factor, that deformation must not silently create, remove, or retype the preserved zeros and poles in the visible domain.

If the user asks for the field, soup, or background to evolve while poles/zeros wander, both must evolve together in the running app. Do not freeze one layer and synthesize motion in the other afterward.

## Capture and delivery

Capture screenshots and moving evidence from the running process. For Android, verify that the installed package remains live during capture and retain logs or equivalent receipts sufficient to establish the executing path.

Post-processing is limited to operations that do not invent or alter demonstrated behavior, such as trimming, container conversion, audio removal, or ordinary encoding/resizing. Do not use transitions, frame synthesis, color grading, stabilization, or interpolation to repair the evidence.

Before presenting a visual artifact as evidence of app behavior, verify all of the following:

1. the exact requested build was installed/launched;
2. the app process was actually running while the frames were captured;
3. the requested backend path, if any, was actually selected;
4. the capture is from a continuous runtime segment rather than a reconstruction;
5. the motion is visually continuous where continuity is intended;
6. established rendering/color behavior has not changed unintentionally;
7. mathematical object identities and requested simultaneous background motion are preserved.

If any of these cannot be established, say exactly what remains unverified. Do not convert missing runtime evidence into a pass by using a mockup, alternate renderer, alternate backend, or post-production.