# Numerical & scientific code checklist

Supplementary correctness axis, applied only when the code under review does array math, optimization, statistics, or automatic differentiation. Findings from this list go in the **Bugs & correctness** tier unless they are pure design/readability points.

## Shapes & broadcasting

- Shape bugs: operations that only work for the shapes in the tests, implicit squeezes/expands, reliance on 1-D arrays behaving like column vectors.
- Broadcasting hazards: an `(n,)` against an `(n, 1)` silently producing `(n, n)`; flag any binary op where the operand shapes aren't obviously compatible by construction.
- Axis arithmetic: hard-coded axis numbers that break under batching; prefer negative axes or named helpers when the code is meant to be batch-polymorphic.

## Dtypes & precision

- Accumulation in float32 where the reduction is long enough to lose precision; integer division or overflow where floats were intended.
- Catastrophic cancellation: subtracting nearly-equal quantities (`log(1 + x)` vs `log1p`, `exp(x) - 1` vs `expm1`, naive variance formulas).
- Comparisons: `==` on floats, tolerances that are absolute where they should be relative (or vice versa), `np.isclose` defaults accepted without thought.

## Stability & conditioning

- `inv(A) @ b` instead of `solve(A, b)`; explicit determinants or inverses where a factorization (Cholesky, QR, LU) is the right tool.
- Log-space where products/likelihoods underflow: prefer `logsumexp`, log-densities, log-space recursions.
- Unguarded `sqrt`/`log`/division by quantities that can hit zero or go slightly negative from round-off (e.g. variances, eigenvalues of a nearly-PSD matrix).

## NaN / inf propagation

- Silent NaN propagation: code that can produce NaN and carries on; decide whether the contract is propagate, raise, or mask -- and make it explicit.
- Reductions that hide NaNs (`nansum` et al.) used as a fix rather than a documented policy.

## Autodiff

- In-place mutation of traced/tracked arrays; Python-side control flow on traced values where the framework needs symbolic branches.
- Non-differentiable points on the likely path (`abs`, `max`, `round`, boolean masking) without a subgradient story.
- Gradient leaks and blocks: missing `stop_gradient`/`detach` where the math requires it, or an accidental one where it doesn't.
- Custom gradients/`Op`s: check the reverse rule against the forward math, not against the code.

## Randomness & reproducibility

- Global RNG state mutated by library code; prefer passed-in generators/keys. Seeds set in one place but not threaded through to all stochastic components.

## Performance idioms

- Python loops over array elements where a vectorized/einsum form exists -- but only flag when the loop is on a hot path; a clear loop over 10 items beats an opaque einsum.
- Repeated factorizations or recomputed invariants inside iterative algorithms (re-solving with the same matrix, re-validating the same inputs each step).

## Contracts

- Tolerances, iteration caps, and convergence criteria as unexplained magic numbers -- name them and put defaults in the docstring per the standard parameter rules.
- Units and scales: interfaces that mix units (log vs natural scale, radians vs degrees, rates vs probabilities) without the name or docstring saying which.
