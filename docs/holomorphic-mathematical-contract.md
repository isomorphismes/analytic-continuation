# Holomorphic explorer mathematical contract

This document states the mathematics of the live `cauchy-field` explorer independently of the particular GPU and Android implementation.

The current contract is **local to the visible region**. It deliberately replaces the earlier requirement that the moving factor be entire on all of `C`.

## 1. Live object

The explorer displays

```text
f_t(z) = R(z) H_t(z)
H_t(z) = exp(q_t(z))
```

where `R` carries the explicit zeros and poles selected by the user:

```text
R(z) = gain * product_i (z - a_i)^(m_i)
              / product_j (z - b_j)^(n_j)
```

The moving field is

```text
q_t(z) = sum_k a_k(t) / (xi_k(t) - z).
```

The `xi_k(t)` are Cauchy sources kept outside a disk containing the entire visible viewport.

## 2. Visible-region invariant

Let `V` be the visible rectangle in complex coordinates, and let `r_view` be the radius of its circumscribed disk centered at the origin.

For the first implementation,

```text
|xi_k(t)| = rho_k(t)
rho_k(t) = 1.8 r_view + 0.35 r_view * sin(...)
```

so

```text
1.45 r_view <= |xi_k(t)| <= 2.15 r_view.
```

Every source therefore remains strictly outside the circumscribed view disk. Hence each kernel

```text
1 / (xi_k(t) - z)
```

is holomorphic on a neighborhood of the visible region. Their finite sum `q_t` is holomorphic there, and

```text
H_t(z) = exp(q_t(z))
```

is holomorphic and nonzero there.

Consequently, **within the visible region**, multiplying by `H_t` neither creates nor removes zeros or poles. The visible divisor is exactly the divisor contributed by `R`.

## 3. This is not a whole-plane meromorphic model

The off-screen singularities are mathematically real even though they are not drawn.

Each `q_t` has poles at the `xi_k(t)`. Because the source weights are nonzero, exponentiating `q_t` produces essential singularities at those points. Thus the global function

```text
R(z) exp(q_t(z))
```

is not a meromorphic function on all of `C` whose only finite singularities are the explicit poles of `R`.

The previous whole-plane design required `q_t` to be entire. That is a different model. It remains a legitimate alternative, but it is not the semantics of this branch.

No documentation, test, or backend should describe the Cauchy-field construction as entire merely because its singularities are off screen.

## 4. Viewport dependence

The source radius is defined from `r_view`, so the hidden source configuration is viewport-relative.

Changing zoom changes `r_view` and therefore changes the source positions used to define `q_t`. In this experimental model, zoom is consequently not a mathematically passive camera operation: it changes the moving field while maintaining the invariant that all Cauchy singularities remain outside the visible region.

If a later design requires zoom to leave the mathematical function fixed, source placement will need a different rule.

## 5. Time evolution

The source trajectories and weights are smooth deterministic functions of elapsed time and source index. Random-looking constants select different phases, angular speeds, wobble rates, amplitudes, and weight rotations for the fixed source population.

The initial source count is

```text
SOURCE_COUNT = 24.
```

The initial weight amplitudes lie approximately in

```text
0.015 <= |a_k(t)| <= 0.08.
```

There is no coefficient search, sample-point disturbance score, accepted-step counter, coefficient budget, or CPU worker ensemble in the mathematical evolution.

The CPU supplies elapsed time. Every fragment evaluates the same `q_t` at its own complex coordinate `z`.

## 6. Exact quantities supplied to Wegert

There is no need to evaluate the complex exponential explicitly for coloring.

For

```text
f(z) = R(z) exp(q(z)),
```

we have exactly

```text
log|f(z)| = log|R(z)| + Re(q(z))
phase(f(z)) = phase(R(z)) + Im(q(z)).
```

The renderer boundary is therefore

```text
explicit zero/pole contribution from R
+ Re(q), Im(q)
-> phase, log modulus
-> canonical Wegert value/color behavior
-> interaction overlays.
```

RGB differences and screen derivatives are not substitutes for complex holomorphy.

## 7. Why the Cauchy family is structurally useful

The kernels

```text
1 / (xi - z)
```

are not basis-free, but they arise directly from the Cauchy-integral picture of holomorphic functions. Moving exterior source data produces a global, smooth deformation felt at every visible point without fitting a small polynomial coefficient vector on the CPU.

This is the practical reason for the experiment. It does not imply that this finite family parameterizes every holomorphic function on the viewport.

## 8. Separation of responsibilities

The live mathematical field owns:

- the explicit Cauchy-source formula;
- source trajectories and complex weights;
- the invariant that all hidden sources stay outside the visible region;
- the resulting `q_t`.

The GPU owns:

- evaluating the source descriptors efficiently for each fragment;
- producing `Re(q_t)` and `Im(q_t)`;
- combining them with the rational zero/pole contribution.

The CPU owns:

- elapsed time;
- visible zero/pole interaction state;
- viewport state;
- Android/EGL integration.

Wegert owns the reusable complex-value / phase / log-modulus to phase-portrait color boundary.

## 9. Interaction invariants

The user-visible circles and X marks retain their mathematical types while moving:

- a zero remains a zero;
- a pole remains a pole;
- dragging changes its position in `R`;
- the Cauchy field does not convert one into the other.

Pinch zoom is currently permitted over the range `0.1` through `32.0`.

## 10. Acceptance

Before treating a build as evidence for this branch, checks should establish at least:

1. the CPU worker/coefficients architecture is absent from the active build;
2. the shader receives elapsed time and evaluates the Cauchy field per fragment;
3. all synthesized source radii remain greater than the circumscribed visible radius;
4. the Cauchy contribution is added to phase/log modulus before the Wegert color boundary;
5. the explicit zero/pole interaction still works;
6. the running APK shows actual frame-to-frame field motion;
7. runtime evidence comes from the app actually executing, not from interpolated or reconstructed frames.

## 11. Whole-plane entire model as an alternative

If the explorer later returns to the stronger requirement that the moving factor be globally nonvanishing entire, then `q_t` must again be entire. Exterior Cauchy poles would not be admissible.

A whole-plane reproducing-kernel model such as a Bargmann-Fock space remains one possible direction. For example, with scale `s`, a value-normalized entire representer can take the form

```text
phi_a(z) = exp((z conjugate(a) - |a|^2) / s^2).
```

That model and the present viewport-relative Cauchy-source model answer different mathematical design questions. They should not be conflated.
