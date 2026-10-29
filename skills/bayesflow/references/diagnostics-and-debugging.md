# Diagnostics and debugging

## Contents

- The validation ladder
- Loss curves
- In-silico diagnostics
- Real data: misspecification and predictive checks
- Symptom table
- Debugging procedure

## The validation ladder

1. Training and validation loss.
2. In-silico checks on fresh simulations: recovery, SBC, coverage, contraction and z-scores. These test the approximator alone, because the simulator is correct by construction.
3. Out-of-distribution check of the observed data in summary space.
4. Posterior predictive checks on the observed data.
5. Where feasible, a reference posterior from MCMC on a few datasets, which separates approximation error from misspecification.

Passing 2 says nothing about 3 to 5. Amortized posteriors are only trustworthy where the simulator places mass, and real data outside that region produce confident nonsense.

## Loss curves

`bf.diagnostics.loss(history)` plots training and validation curves (`bf.diagnostics.plots.loss` is the same function).

- A smooth decrease to a plateau is healthy.
- A widening gap between training and validation loss means overfitting. Raise the simulation budget, switch to online training, or shrink the network.
- A loss still falling at the last epoch means more epochs are needed. With the default cosine schedule, run the whole budget again in one `fit_*` call.
- NaN or exploding values come from pathological simulations (extreme tails, unbounded values) or missing normalization. Clip in the simulator, log-transform, or standardize.
- For flow matching, diffusion and consistency models the loss stops tracking quality after the initial drop. Judge them by in-silico diagnostics only.
- Coupling flow loss is a negative log density and is directly comparable across runs on the same data.

## In-silico diagnostics

```python
test_data = workflow.simulate(300)
samples = workflow.sample(num_samples=1000,
                          conditions=test_data,
                          batch_size=50)

figures = workflow.plot_default_diagnostics(test_data=test_data, samples=samples)
table = workflow.compute_default_diagnostics(test_data=test_data, samples=samples)
```

Passing `samples=` reuses draws instead of resampling. The default figures are `losses`, `recovery`, `calibration_ecdf`, `coverage` and `z_score_contraction`. The table has NRMSE, Log Gamma, Calibration Error and Posterior Contraction per parameter. Its warning about `normalize='prior'` is informational. For model comparison the defaults switch to confusion matrix and calibration curves (PMP rules) or calibration, pairwise Bayes factors and BF recovery (BF rules, recovery needs `true_log_bfs_fn`).

Individual plots take `estimates=` (draws dict) and `targets=` (the simulated dict) plus `variable_keys`, `variable_names`, and `test_quantities`:

- `recovery`: posterior median against truth with credible bars. Bias appears as curvature or offset. Uniformly wide bars mean weak information for that parameter.
- `calibration_ecdf(..., difference=True)`: the preferred SBC plot. The rank counts posterior draws below the truth. A difference curve on one side of zero across the middle ranks means bias: below zero, truths rank high and the posterior sits too low, and above zero, the posterior sits too high. An S shape means miscalibrated width: a rise then a fall (ranks piled at both ends) is overconfident, a dip then a rise (ranks piled in the middle) is underconfident. The user guide's "above means overconfident" shorthand conflates the two. It is more sensitive than `calibration_histogram`, whose bands are conservative and which warns when simulations per draw are below 20.
- `coverage`: empirical against nominal interval coverage. Below the diagonal means intervals are too narrow.
- `z_score_contraction`: contraction near 1 with z-scores centered on 0 is the target. Contraction near 0 means the data barely inform the parameter. High contraction with large absolute z means overconfident and wrong.
- `pairs_posterior(estimates=, targets=, dataset_id=0)`: one dataset's joint posterior, revealing correlation and multimodality.
- Point estimators use `recovery_from_estimates` and `calibration_ecdf_from_quantiles(..., quantile_levels=q)`.

Interpretation rules:

- Perfect recovery is not the target. Truths should sometimes fall in the tails. If they never do, intervals are too wide.
- Absolute z-scores above 3 usually mean undertraining.
- Flat recovery plus near-zero contraction has two causes, undertraining or non-identifiability from the chosen observables. A longer run, a larger summary network or added informative features distinguish them. In the SIR example two parameters stayed flat because the observables do not identify them.
- Check calibration across the range of every context variable (N, T, design). Calibration at one N says nothing about another.
- SBC on derived quantities is stricter than on parameters. Pass `test_quantities={"name": fn}`, where `fn` maps a dict with a leading batch axis to a 1-D array. For data-dependent quantities (joint log likelihood, predictive RMSE), tile the conditions across the draw axis and merge them into the draws dict first:

```python
conditions = {k: v for k, v in test_data.items() if k not in parameter_names}
tiled = keras.tree.map_structure(lambda t: np.repeat(np.expand_dims(t, axis=1), num_samples, axis=1),
                                 conditions)
bf.diagnostics.calibration_ecdf(estimates=samples | tiled,
                                targets=test_data,
                                test_quantities={"log_lik": joint_log_likelihood},
                                variable_keys=[],
                                difference=True,
                                rank_type="distance")
```

`variable_keys=[]` shows only the custom quantities. An affine coupling flow can pass parameter SBC and fail log likelihood SBC.

Custom plots plug in through `workflow.plot_custom_diagnostics(test_data, plot_fns={"name": fn}, num_samples=...)`, where `fn(samples, test_data, variable_keys=None, variable_names=None, **kwargs)` returns a figure.

## Real data: misspecification and predictive checks

Summary-space check:

```python
mmd_observed, mmd_null = bf.diagnostics.summary_space_comparison(observed_data=observed,
                                                                 reference_data=workflow.simulate(1000),
                                                                 approximator=workflow.approximator)
bf.diagnostics.mmd_hypothesis_test(mmd_null=mmd_null, mmd_observed=mmd_observed)
```

An observed MMD far in the null's tail means the observed data look unlike any simulation, so the posterior is an extrapolation. `approximator.sample(..., return_summaries=True)` gives the raw summaries for direct plots against simulated summaries.

Posterior predictive check: re-simulate from posterior draws and compare with the observed data on domain-relevant features. About 50 draws suffice visually.

```python
resims = np.stack([workflow.simulate(1, parameters=draw)["observables"].squeeze()
                   for draw in samples["parameters"][dataset_id, :50]])
```

For function-based simulators, call the likelihood function directly with each draw. Built-in simulators accept fixed parameters as `sample(1, parameters=draw)`.

A model that is well calibrated on simulations and disagrees with MCMC or predictive checks on real data points to a simulation gap. The likelihood, the prior range, or the data-generating context does not match the observed data. More training does not fix it. Change the simulator: widen priors, add the missing noise or structure, simulate the observation process including its selection and missingness, or condition on the context that varies in the real data. Then re-run the in-silico checks.

## Symptom table

| Symptom | Likely cause | Check or fix |
|---|---|---|
| `ValueError` or shape error at first batch | Summary input not 3-D, scalar `meta_fn` value not broadcast, mismatched concat shapes | `adapter(simulator.sample(4))` and print shapes. Add `as_set`, `as_time_series` or `broadcast` |
| Training silently ignores a variable | Key never renamed to a routing key, or `adapter=` plus naming kwargs | `print(adapter)`, inspect `dataset[0]` keys |
| dtype errors or float64 rejected on GPU | Missing `convert_dtype`, JAX x64 enabled | Add `convert_dtype("float64", "float32")`, wrap in `jax.enable_x64(False)` |
| Backend warning at import | keras imported before bayesflow | Set `KERAS_BACKEND`, import bayesflow first, restart the kernel |
| Very slow first epochs on JAX | Batch shapes vary (varying N) | Expected recompilation. Bucket N or accept warmup |
| Online training is slow | Simulator-bound | Time `simulator.sample(batch_size)`. Use a batched `LambdaSimulator`, `sample_parallel`, or pre-simulate and `fit_offline` |
| Posterior draws violate support | Missing `constrain` | Constrain bounded parameters before concatenation |
| Draws out of order or mislabeled | `concatenate` order differs from assumed order | Use the dict keys from `sample`, or `split=True` |
| Overconfident in SBC | Undertrained, summary too small, offline overfitting | More simulations and epochs, larger `summary_dim`, online training |
| Underconfident in SBC | Network too small for posterior complexity | Spline coupling or flow matching, deeper subnet, longer training |
| SBC ECDF difference on one side of zero | Posterior biased for that parameter | Compare runs that differ in one setting (standardization, data size), check the parameter's transform and support |
| Multimodal posterior collapsed to one mode | Affine coupling flow | `FlowMatching`, `DiffusionModel`, or `transform="spline"` |
| Good in-silico, bad on real data | Simulation gap or OOD data | Summary-space MMD, predictive checks, fix the simulator |
| Second `fit_*` call made things worse | Schedule restarted with warmup | One call with the full budget, or `keep_optimizer=True` |
| Loaded model gives different draws | Version change, weights-only load, custom class not registered | Pin version, save full `.keras`, `@serializable`, compare stored outputs |
| PyMC model suddenly float32 | `NeuralDistribution` set `floatX` | Expected. Build float64 models in a separate process |
| Multiprocessing PyMC sampling hangs | Fork after JAX initialized | `cores=1` or spawn context |
| `rejection_sample` never returns | Predicate rejects nearly everything | Loosen the predicate or reparameterize the prior |

## Debugging procedure

1. Shapes first. Print `simulator.sample(4)`, `adapter(...)` and `dataset[0]` before training anything.
2. Shrink the problem. Fix all but one or two parameters, train a point estimator or a small coupling flow for a few epochs, and confirm recovery moves. Point networks need one pass and iterate in seconds.
3. Separate information from capacity. If hand-crafted summaries passed as `inference_conditions` recover a parameter and the learned summary does not, the summary network is the bottleneck. If neither recovers it, the observables do not identify it. Engineered per-dataset features (variances, quantiles, fitted statistics) passed alongside the raw set often help more than a larger network.
4. Scale up one axis at a time: simulation budget, epochs, summary size, inference network expressiveness. Re-run SBC after each change.
5. Before real data, run the summary-space check and compare against MCMC on a handful of datasets where MCMC is feasible.

Timing anchors from the examples: point estimation trains in seconds, a set-transformer NPE on small data in 2 to 5 minutes on a laptop, an NLE spline flow in 4 to 5 minutes on CPU or about 20 seconds on GPU, image diffusion in about 10 minutes on GPU. A pooled set-transformer NPE in this environment ran about 22 ms per batch on an Apple M4 Max GPU through jax-metal.
