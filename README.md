# Analytic Continuation

This repository currently contains one useful experiment: a native Android
holomorphic-random explorer.

The live program moves a near-identity holomorphic map

```text
h(w) = w + a2 w^2 + a3 w^3 + ... + a6 w^6
```

through coefficient space. Three small worker threads propose low-disturbance
directions, the render thread accepts only steps that stay inside the current
derivative and preimage bounds, and an OpenGL ES fragment shader evaluates the
result for every pixel. The motion changes the function; it is not a hue
animation.

This is **not yet analytic continuation**. It does not transport a Taylor germ,
derive a new local expansion in each overlapping disc, or track monodromy.
Those are the minimum requirements before a future feature should use the name
`continuation`.

## Repository boundary

[Wegert](https://github.com/isomorphisms/wegert) owns:

- complex-value to Wegert-color conversion;
- rational zero and pole state;
- zero and pole editing and markers; and
- the ordinary phase-portrait interface.

This repository owns the experimental time-varying holomorphic deformation and
the checks that keep that deformation inside its stated bounds. It must not grow
a second general zero/pole editor, a second phase-portrait application, or a
second copy of Wegert behavior.

The current Android implementation still contains a temporary rational portrait
adapter inherited from the false starts. It is isolated in
`analytic_continuation.c`, which the holomorphic wrapper currently includes.
Removing that adapter without losing the working explorer is the next native
cleanup boundary; see [`docs/cleanup.md`](docs/cleanup.md).

## Build and checks

The Android project is under `android/`. It uses a C `NativeActivity`, EGL, and
OpenGL ES 3; no Python runtime, desktop animation engine, generated movie, or
Java UI owns the live interaction.

The small repository checks run with:

```sh
python -m unittest discover -s tests -v

cc -std=c11 -Wall -Wextra -Werror \
  -Iandroid/app/src/main/cpp \
  tests/test_holomorphic_walk.c \
  android/app/src/main/cpp/holomorphic_walk.c \
  -pthread -lm \
  -o /tmp/test-holomorphic-walk
/tmp/test-holomorphic-walk
```

Android release notes are in [`docs/github-apk-release.md`](docs/github-apk-release.md),
[`docs/google-play-release.md`](docs/google-play-release.md), and
[`fdroid/README.md`](fdroid/README.md).

## Historical experiments

Movie rendering, closed-form function cards, rational convergence-disc reveal,
rigidity guessing, Ithon touch placement, underdetermined completion, and the
CPU local-kernel perturbation prototypes remain available in Git history and
old branches. They are not active interfaces and should not be merged back as a
bundle. A useful idea must be reintroduced through the ownership boundary above
and must say whether it is visualization, holomorphic deformation, or actual
germ continuation.
