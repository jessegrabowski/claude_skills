# Bayesian Modeling

These conventions override the pymc-agent-skills examples where they conflict.

Never hand-roll posterior statistics. Use arviz (`az.hdi`, `az.summary`, `az.loo`, `az.loo_pit`, `az.plot_ppc_dist`), the model class's own posterior methods, or xarray reductions over `chain` and `draw`. Never ravel draws into numpy to compute quantiles, means, or coverage by hand. Report HDIs.

Hierarchical standard deviations get `pm.Gamma(alpha=2, beta=rate)`, because HalfNormal puts its mode at total pooling. Other positive scales get a Gamma fitted with `preliz.maxent`, with a comment above the prior recording the call and its result, for example `# maxent(Gamma, [0.0005, 0.015], 0.9 mass) -> alpha=2.2287, beta=286.0`. Observation noise may stay HalfNormal.

Write prior parameters inline in the distribution call, not as named constants. Every labeled axis uses `dims` with an explicitly built coord, including plain range indices. Effects over a closed set (the full rating ladder) use `ZeroSumNormal`, and effects over an open set (issuers) use `Normal`.

Compute and save `log_likelihood` at fit time. Seed with `sum(map(ord, "<phrase>"))`, never 42. Fit ADVI with the pymc-extras ADVI module (`fit_advi`, `Trainer`), not `pm.fit`.
