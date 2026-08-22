# Underdetermined completion: vibrating domain

This branch explores a visual rule for a complex function that the user has not
yet specified completely.

## Analytic exploration family

A finite list of point values does not determine an arbitrary analytic
function.  The vibrating completion therefore no longer pretends that eight
point constraints exhaust eight polynomial coefficients.

The renderer now writes the displayed function as

    f(z) = A(z) + V(z) W(z)

with

    V(z) = product(z - z_i)

for every constrained domain point `z_i`.

`A` is the anchored analytic function already accepted by the user.  `W` is a
small, damped random sum of complex exponentials

    W(z) = sum a_k exp(lambda_k z).

The nonzero `lambda_k` are seeded once per experiment.  Even a finite sum of
these modes is an entire, generally non-polynomial function.  More importantly,
adding a point constraint does not consume one of the exponential modes: every
mode remains available, multiplied by the new vanishing factor.

The finite mode count and the twelve stored point constraints are implementation
budgets for a phone renderer, not mathematical dimensions of the analytic
family.

## Exact constraints and no-jump locking

Because `V(z_i) = 0`, every future perturbation `V W` vanishes exactly at every
locked point.  The dot/line gesture therefore still means

    dot domain:       f(z) = 0
    line terminus:    f(z) = 1

and those values remain fixed while the rest of the portrait moves.

A tap means "lock what I see here."  Before the new point is recorded, the
current `V W` perturbation is folded into `A`.  Algebraically this rewrites the
same entire function; it does not merely preserve the tapped pixel.  The whole
current frame is therefore the anchor for subsequent motion.  A requested zero
or one value then adds a multiple of the old `V`, which preserves every older
constraint exactly.

A zero/one pair is accepted atomically: if either endpoint is invalid, the
entire state rolls back.

## Interaction

Single tap locks the current value.  One-finger drag previews and creates the
zero/one dot-line symbol.  Two-finger pinch pans and zooms.  Three fingers reset
the experiment.  Ordinary locked values remain ring markers; the zero/one pair
is represented by its dot and line instead of duplicate rings.

## Damping

The random exponential amplitudes follow the same mean-reverting walk as the
prototype.  Motion is multiplied by

    1 / sqrt(1 + 0.55 * number_of_constraints).

Thus every added point calms the portrait, but no finite number of constraints
is described as exhausting the analytic family.  At eight constraints the
function still has visible legal motion away from the constrained points.

## GPU cost

The GLES3 shader uses four analytic modes.  For each pixel it evaluates four
short polynomial prefactors with Horner's rule, four complex exponentials, one
vanishing product over the stored constraints, and the existing domain-coloring
and dot/line overlay.  All stochastic updates and constraint bookkeeping remain
on the CPU once per frame or gesture.

The polynomial prefactors are bookkeeping for the anchored exponential modes:
when current motion is frozen into `A`, multiplying an exponential by the
current `V` only raises that mode's polynomial prefactor.  The function itself
remains non-polynomial as long as a nonzero-frequency exponential mode is
present.

Like every float renderer of a nonconstant entire function, extreme pan/zoom
can eventually exceed the numerical range of `exp`.  The branch deliberately
does not clamp the exponential argument, because such a clamp would itself
break analyticity.  The intended interactive window stays well inside the
float-safe range for the seeded frequencies.
