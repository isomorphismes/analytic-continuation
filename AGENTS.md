# Agent instructions

## Runtime video evidence

When a task asks for a video, MP4, GIF, screen recording, or other moving demonstration of this app or renderer, the video must come from the app actually running.

For a tagged release, install and launch the APK built from that exact tag. For development work, identify the exact commit/build being run. Capture the live render loop with Android/emulator screen recording or direct frame capture from the running process.

Do not substitute any of the following for runtime footage:

- AI-generated still images or generated animation frames;
- cross-fades between screenshots or keyframes;
- interpolation, optical-flow synthesis, pan/zoom, or other fake motion;
- a hand-made reconstruction that merely resembles the app;
- frames produced by a separate renderer while claiming they came from the APK.

If the requested motion is not present in the current app, change the app, build a new APK, run that build, and record the resulting runtime behavior. Do not manufacture the missing behavior in post-production.

When the visualization contains poles and zeros/holes, movement is not a type change. A pole remains a pole and a zero/hole remains a zero/hole unless the mathematical model is explicitly being changed. Poles and zeros may wander long distances, cross, and exchange regions while retaining their identities.

Post-processing is limited to operations that do not invent or alter the demonstrated behavior, such as trimming, container conversion, audio removal, or ordinary encoding/resizing. Do not use transitions to conceal discontinuities between unrelated runs.

A runtime video should retain enough provenance to reproduce it:

- repository and commit/tag;
- APK/build artifact used;
- device or emulator target;
- launch and recording procedure;
- raw capture or an unambiguous path to it when practical.

Before presenting a video as evidence of app behavior, verify that the app process was actually running while the demonstrated frames were captured. If the app cannot be run, say so. Do not silently replace runtime evidence with a mockup.