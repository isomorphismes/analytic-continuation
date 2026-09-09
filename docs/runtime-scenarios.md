# Runtime scenarios

The Android explorer separates five concerns that used to be mixed in the `NativeActivity` engine:

- `scene`: the mathematical divisor and camera zoom;
- `field_evolution`: the continuously changing background field;
- `motion`: continuous trajectories for visible zeros and poles;
- `presentation`: marker geometry, controls, and whether touch interaction is enabled;
- `scenario`: data that composes the other four for one run.

The default `android/app/src/main/assets/scenario.conf` is the ordinary interactive explorer. Video or experiment work should normally change scenario data, not rewrite `analytic_continuation_random.c` or patch the fragment shader from a capture script.

## Scenario format

The file is line-oriented `key=value` text. Blank lines and `#` comments are ignored.

A minimal normal configuration is:

```text
name=interactive
presentation=interactive
field=entire
field_speed=0.30
field_budget=1.20
motion=none
```

A stronger clean moving presentation can instead select the wandering off-screen-pole field and describe the initial divisor and motion explicitly:

```text
name=two-pair-wander
presentation=clean
marker_radius=5.0
marker_stroke=1.8

field=wandering_offscreen_poles
field_speed=0.42
field_budget=6.0

motion=wander
seed=7319
wander_speed=0.08
wander_bound=1.7

zero=-0.8,0.2
zero=0.0,-0.6
zero=0.7,0.4
pole=0.8,-0.2
pole=0.1,0.6
pole=-0.6,-0.3

exchange=zero,0,pole,2,4.0,6.0,ccw
exchange=zero,2,pole,0,14.0,6.0,cw
```

Supported keys are:

- `name`: receipt/log name for the scenario;
- `zero=x,y`, `hole=x,y`, `pole=x,y`: initial visible factors; the first explicit factor line replaces the normal one-zero/one-pole default;
- `zoom`: mathematical viewport zoom;
- `presentation=interactive|clean`;
- `show_controls=true|false`;
- `interaction=true|false`;
- `marker_radius`, `marker_stroke`: marker geometry in pixels;
- `field=entire|wandering_offscreen_poles`;
- `field_speed`: speed of the `exp(q)` holomorphic walk;
- `field_budget`: coefficient budget used both by the direction search and by the applied `exp(q)` evolution;
- `motion=none|wander`;
- `seed`: deterministic wander seed;
- `wander_speed`: continuous non-lockstep drift speed;
- `wander_bound`: soft restoring boundary in complex-plane coordinates;
- `exchange=kind,index,kind,index,start,duration,cw|ccw`.

`clean` presentation hides placement controls, disables touch interaction, and uses smaller marker geometry. It does not alter the mathematical field or fabricate frames.

## Exchange semantics

An exchange is a real motion of two existing mathematical objects. At the event start, their current positions are captured. Both then rotate through the same half-circle about their midpoint in the requested direction. At the end they occupy each other's starting positions exactly.

The objects retain their types throughout: a pole remains a pole and a zero/hole remains a zero/hole. Different exchanges can involve nonadjacent factors and occur at different times. Factors that are not currently participating in an exchange can continue deterministic random-looking wander, so the whole divisor need not move in lockstep.

The motion module advances persistent state with bounded time steps. Capture scripts should not replace this with ADB swipes, frame interpolation, cross-fades, or independently generated positions.

## Field modes

`field=entire` is the ordinary whole-plane perturbation

```text
R(z) exp(q(z))
```

with the existing three-worker direction search driving the coefficients of `q`. This mode is entire and nonzero apart from the visible rational divisor `R`.

`field=wandering_offscreen_poles` adds the twenty-four procedural remote poles from the stronger lava-lamp experiment. They stay outside the circumscribed visible region and wander continuously there while the `exp(q)` field continues to evolve. Their contribution is therefore holomorphic and nonzero on the visible region, but unlike `exp(q)` it is not entire on the whole complex plane. The distinction is explicit in the scenario rather than hidden in a special-purpose APK path.

The field state and cadence are independent of visible-divisor motion. A video can therefore choose the stronger off-screen-pole soup while separately deciding which visible factors wander, when pairs exchange, and how large the markers are.

## Runtime acceptance

`scenarios/video-demo.conf` is a clean scenario used by CI to exercise the same path intended for presentation videos: smaller markers, no placement controls, the stronger off-screen-pole field, background evolution, random non-lockstep wander, and two scheduled half-circle exchanges. CI builds this by replacing only `scenario.conf` before the APK build; it does not rewrite the native engine or shader.
