# Bayesian Modeling

These conventions override the pymc-agent-skills examples where they conflict.

Never hand-roll posterior statistics. Use arviz (`az.hdi`, `az.summary`, `az.loo`, `az.loo_pit`, `az.plot_ppc_dist`), the model class's own posterior methods, or xarray reductions over `chain` and `draw`. Never ravel draws into numpy to compute quantiles, means, or coverage by hand. Report HDIs.

Hierarchical standard deviations get `pm.Gamma(alpha=2, beta=rate)`, because HalfNormal puts its mode at total pooling. Other positive scales get a maxent Gamma (see Prior elicitation). Observation noise may stay HalfNormal.

Write prior parameters inline in the distribution call, not as named constants. Every labeled axis uses `dims` with an explicitly built coord, including plain range indices. Effects over a closed set (the full rating ladder) use `ZeroSumNormal`, and effects over an open set (issuers) use `Normal`.

## Prior elicitation

Elicit priors in the model code, not in comments. A prior elicited by maximum entropy is the PreliZ call itself, turned into the PyMC variable with `.to_pymc`:

```python
error_sigma = pz.maxent(pz.Gamma(), lower=0.005, upper=0.05, mass=0.9).to_pymc("error_sigma",
                                                                               dims="observed_state")
```

Turn off PreliZ's automatic plots once, right after importing it, with `pz.rcParams["plots.show_plot"] = False`, instead of passing `plot=False` to every call.

The bounds and mass are the specification, so they are what the code states. Never run maxent elsewhere and paste its fitted parameters into the model, and never write the call as a comment above hardcoded numbers. The same holds for every other family maxent supports, such as Beta for coefficients in (0, 1).

## Fitting

Compute and save `log_likelihood` at fit time. Define one `SEED = sum(map(ord, "<phrase>"))` in the notebook's import cell and pass it to every seeded call, never 42. Fit ADVI with the pymc-extras ADVI module (`fit_advi`, `Trainer`), not `pm.fit`.
