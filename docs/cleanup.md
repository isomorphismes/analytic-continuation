# Cleanup boundary

## Goal

Reduce the repository to the holomorphic-random explorer that is actually worth
keeping, while leaving Wegert responsible for coloring, rational factors,
markers, and the ordinary phase portrait.

This cleanup does not erase history. Git retains the discarded experiments.
The point is to stop treating every false start as a supported live interface.

## Removed in the first cleanup slice

| Removed surface | Reason |
| --- | --- |
| Python `movie-v1` package and CLI | It described a retired renderer contract and did not drive the Android app. |
| Closed-form function registry and examples | They were reference material for the retired movie/disc-reveal route, not inputs to the live explorer. |
| Python and C rational disc planners | They revealed discs around a closed-form evaluator but did not transport a germ. Calling them continuation was misleading. Wegert already owns the rational preview. |
| Copied factor, gesture, snap, and formula-overlay headers that no shipping source included | Their tests created green evidence for dead interfaces. The maintained versions belong in Wegert. |
| Rigidity and guided-movie plans | They were speculative product directions, not dependencies of the useful experiment. |

## Keep

- the native EGL/OpenGL ES application shell;
- the near-identity degree-six holomorphic map;
- the three-worker bounded coefficient search until the GPU-wide replacement is
  accepted;
- explicit derivative-budget and factor-preimage safety checks used by that
  experiment;
- the Wegert color parity fixture while the temporary adapter still exists; and
- Android build, emulator, and release evidence for the exact APK being tested.

## Next native extraction

The remaining false-start coupling is visible rather than hidden:

```text
analytic_continuation_random.c
  includes analytic_continuation.c
    owns temporary rational factors, markers, lasso UI, and Wegert adapter
```

Replace that with three explicit pieces:

1. `holomorphic_field`: produces a bounded deformation descriptor or direct
   phase/log-modulus contribution;
2. `explorer_shell`: owns Android lifecycle, camera, pause, and touch routing;
3. `wegert_adapter`: the smallest replaceable boundary needed to display a
   complex value with Wegert coloring, with no factor editing in this app.

The extraction is complete only when:

- the shipping source no longer textually includes another `.c` file;
- zero/pole placement, dragging, cancellation, markers, and polynomial text are
  absent from this repository's live interface;
- no copied Wegert palette or factor implementation can drift here;
- the APK opens directly into the holomorphic-random explorer;
- Android Back/system navigation exits; and
- pause, camera movement, lifecycle restart, and a visible flowing field have
  on-device evidence.

## Future analytic continuation

A future continuation mode starts from a base point and Taylor germ, transports
that germ through overlapping local expansions, and records branch/monodromy
state. A closed-form evaluator with a disc-shaped reveal mask is only a preview
and must not occupy that interface.

The repository should not accept new Manim/Manimi runtime work, new rational
factor UI, or new `refC` dependencies while that boundary is unsettled.
