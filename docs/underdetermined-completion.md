# Underdetermined completion: vibrating domain

This branch explores a visual rule for a complex function that the user has not
yet specified completely.

## Finite exploration family

An arbitrary analytic function is still infinitely underdetermined after any
finite list of point values.  The interactive renderer therefore needs an
explicit finite exploration family.  The first prototype uses complex
polynomials of degree at most seven: eight complex coefficients.

If the user has fixed

    f(z_0) = w_0, ..., f(z_(m-1)) = w_(m-1),

write every still-allowed polynomial as

    f(z) = I(z) + V(z) q(z)

where `I` is the degree-`m-1` interpolating polynomial and

    V(z) = product(z - z_i).

`V` is zero at every fixed domain point, so changing `q` can never disturb a
value the user has already supplied.  With maximum degree seven, `q` has
`8 - m` complex coefficients.  Every independent point removes one complex
degree of freedom.  At eight points the family is completely determined.

## Interaction rule

The first useful gesture can be "lock what I see here":

1. Evaluate the currently displayed completion at the tapped domain point.
2. Add that `(domain, value)` pair as a constraint.
3. Re-express the *same current polynomial* in the smaller affine family.
4. Continue the random walk only in the remaining free coefficients.

Step 3 matters visually: adding a point must not make the picture jump.  It
changes which future motions are legal, not the function shown on the locking
frame.

Exact target-value gestures can use the same representation later.  In
particular a marker may impose `f(z)=0`, `f(z)=1`, or any other chosen complex
value rather than locking the current value.

## Motion

The random walker is mean-reverting and bounded in practice.  Its per-frame
noise is multiplied by the square root of the remaining freedom fraction.
Thus the portrait becomes quieter for two independent reasons:

- fewer complex coefficients are allowed to move;
- each remaining coefficient moves less as the family approaches a unique
  completion.

This damping is a visual design choice, separate from the mathematical fact
that the allowed affine space loses one complex dimension per independent
point.

## GPU cost

The fragment shader receives eight complex coefficients and evaluates the
polynomial with Horner's rule.  That is eight complex multiply-adds per pixel.

The existing rational domain-coloring shader can loop over as many as 64 zeros
and 64 poles, including distances, arguments, and logarithms.  The completion
evaluation is therefore small compared with the work the current shader already
accepts.  The random walk and interpolation happen once per frame or once per
tap on the CPU, not once per pixel.

If degree seven is visually too restrictive, the same representation can move
to a larger polynomial or another finite analytic basis.  The important
contract is that the free basis functions vanish at every user-fixed point.
