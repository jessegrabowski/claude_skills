---
name: bayesflow
description: Build, train, validate and debug amortized simulation-based inference with BayesFlow 2.x (Keras 3 on JAX, PyTorch or TensorFlow). Use whenever the task involves BayesFlow, amortized Bayesian inference, simulation-based inference (SBI), neural posterior estimation (NPE), neural likelihood estimation (NLE), neural ratio estimation (NRE), learned summary statistics, amortized model comparison, normalizing flows, flow matching or diffusion models used as posterior approximators, or replacing ABC or MCMC with a trained network, even when the user does not name the library. Also use when wiring a BayesFlow approximator into PyMC as a likelihood, or when a BayesFlow posterior disagrees with MCMC.
metadata:
  tags: [bayesflow, sbi, amortized-inference, keras, jax, bayesian]
---

# BayesFlow

BayesFlow trains neural networks on simulated `(parameters, data)` pairs so that, after training, posterior draws for any new dataset cost one forward pass. The trained object is an amortized approximator, and its quality is only as good as the simulator coverage, the summary statistics and the training budget. Every result needs in-silico validation before it touches real data.

Written against BayesFlow 2.0.14. The user guide and the installed source disagree in places (listed under "Doc versus source" below). Check `inspect.signature` on the installed object before relying on any default.

## Pipeline

```
simulator.sample(B) -> dict of numpy arrays, leading batch axis
  -> Adapter (dict -> routing keys, float32, constraints)
  -> Approximator = summary network (optional) + inference network
  -> Workflow (optimizer, training loop, checkpointing, diagnostics)
```

The adapter routes by key name. Only these keys reach the networks: `inference_variables` (the target), `inference_conditions` (fed straight to the inference network), `summary_variables` (fed through the summary network, whose output joins the conditions), plus the masks `sample_weight`, `summary_attention_mask`, `summary_mask`, `inference_attention_mask`, `inference_mask`. A hand-built adapter passes any other key through untouched and the networks ignore it.

NPE puts parameters in `inference_variables` and data in `summary_variables` or `inference_conditions`. NLE reverses the roles: data become `inference_variables` and parameters become `inference_conditions`.

## Environment setup

- Set `os.environ["KERAS_BACKEND"]` before the first `import bayesflow`, and import bayesflow before keras. With several backends installed BayesFlow picks JAX, then PyTorch, then TensorFlow. Importing keras first freezes keras on its own default and BayesFlow only logs "Automatic backend selection failed".
- On the torch backend, importing bayesflow calls `torch.autograd.set_grad_enabled(False)` globally. Custom torch training loops must run inside `with torch.enable_grad():`.
- Pin the BayesFlow version per project. Checkpoints can load without error across versions and still produce wrong output.
- BayesFlow 2.0.14 requires numpy>=2.5.1, keras>=3.15, pandas>=3.0.5. In a PyMC environment this can force numba and pytensor past their declared pins. Check `pip check` after installing.
- Training data and weights are float32. Every adapter needs `.convert_dtype("float64", "float32")` unless the workflow builds the default adapter, which adds it.

### Sharing a process with PyMC or JAX x64

PyMC and BlackJAX often enable `jax_enable_x64`. Apple Metal (`mtl`) and most GPU paths reject float64. Build, fit and sample inside one context:

```python
import jax

with jax.enable_x64(False), jax.default_device(jax.devices("mtl")[0]):
    workflow = bf.BasicWorkflow(...)
    history = workflow.fit_offline(data=training_data,
                                   epochs=50,
                                   batch_size=256)
    posterior = workflow.sample(num_samples=1000,
                                conditions=observed)
```

`bayesflow.wrappers.pymc.NeuralDistribution` sets `pytensor.config.floatX` to Keras' float (float32) for the whole process on construction. Any PyMC model built afterwards in the same session runs in float32. The wrapper's JAX bridge is the supported path. The ratio-estimation example states PyMC integration is supported only on the JAX backend.

A failed import of bayesflow, blackjax or jax plugins can leave half-initialized modules in `sys.modules`. Restart the kernel instead of re-importing.

## Choosing the approximator

| Goal | Approximator / workflow | Inference network |
|---|---|---|
| Posterior draws p(theta given x) | `ContinuousApproximator`, `BasicWorkflow` | `CouplingFlow` (fast, exact density), `FlowMatching` (multimodal, complex), `DiffusionModel` (most flexible, needed for composition, guidance and masking) |
| Cheap point summaries (mean, quantiles, MVN) | `ScoringRuleApproximator` (picked automatically by `BasicWorkflow` for a `ScoringRuleNetwork`) | `PointNetwork`, `ScoringRuleNetwork(scoring_rules=...)` |
| Likelihood p(x given theta) for use inside PyMC | `ContinuousApproximator` in NLE mode, then `NeuralDistribution` | `CouplingFlow(transform="spline")` |
| Likelihood-to-evidence ratio for PyMC | `RatioApproximator` (contrastive NRE, `K` near `batch_size / 2`) | `MLP` |
| Which model generated the data | `ModelComparisonWorkflow` / `ModelComparisonApproximator` | classifier `subnet="mlp"` |
| Joint trajectories theta_{1:T} | `AutoregressiveApproximator` | encoder with `return_sequences=True` plus `RecurrentDecoder` or `TransformerDecoder` |
| Many datasets sharing global parameters | `CompositionalWorkflow` | `DiffusionModel` only |
| Network uncertainty, architecture comparison | `EnsembleWorkflow` / `EnsembleApproximator` | any mix |

Summary network by data shape: exchangeable sets `(B, N, D)` use `SetTransformer` or the cheaper `DeepSet`. Ordered sequences `(B, T, D)` use `TimeSeriesTransformer` (default), `TimeSeriesNetwork` (conv plus GRU, lighter) or `FusionTransformer`. Images `(B, H, W, C)` use `ConvolutionalNetwork`. Several modalities use `FusionNetwork(backbones={...}, head=...)`. Fixed-length low-dimensional data, or hand-crafted statistics, go straight to `inference_conditions` with no summary network. Start `summary_dim` at about 3 times the number of parameters, and never below the number of parameters.

Details, sizes and defaults: `references/networks.md`.

## Minimal NPE

```python
import os

os.environ["KERAS_BACKEND"] = "jax"

import bayesflow as bf
import numpy as np


def prior():
    return dict(mu=np.random.normal(),
                sigma=np.random.gamma(shape=2.0, scale=0.5))


def likelihood(mu, sigma, N):
    return dict(x=np.random.normal(loc=mu, scale=sigma, size=N))


def meta():
    return dict(N=np.random.randint(10, 100))


simulator = bf.make_simulator([prior, likelihood], meta_fn=meta)

adapter = (
    bf.Adapter()
    .broadcast("N", to="x")
    .as_set("x")
    .constrain("sigma", lower=0)
    .sqrt("N")
    .convert_dtype("float64", "float32")
    .concatenate(["mu", "sigma"], into="inference_variables")
    .rename("x", "summary_variables")
    .rename("N", "inference_conditions")
)

workflow = bf.BasicWorkflow(simulator=simulator,
                            adapter=adapter,
                            summary_network=bf.networks.SetTransformer(summary_dim=8),
                            inference_network=bf.networks.FlowMatching())

history = workflow.fit_online(epochs=50,
                              num_batches_per_epoch=200,
                              batch_size=64,
                              validation_data=300)

test_data = workflow.simulate(300)
figures = workflow.plot_default_diagnostics(test_data=test_data, num_samples=500)
```

`posterior = workflow.sample(num_samples=1000, conditions={"x": x_obs[None, :], "N": x_obs.size})` returns a dict keyed by the original names (`mu`, `sigma`), each shaped `(num_datasets, num_samples, dim)`, back-transformed through the adapter's inverse. A single dataset still needs a leading axis of 1.

## Working sequence

1. Simulator. Return dicts, and name function arguments after keys produced earlier in the list. Draw `simulator.sample(4)` and print every shape. Scalars come back `(B, 1)`, and `meta_fn` outputs come back as unbatched scalars shared by the whole batch.
2. Adapter. Apply it to that sample with `adapter(sample)` and print the routed shapes before any training. Summary networks need 3-D (or 4-D image) input, so use `.as_set` or `.as_time_series` for 1-D per-dataset arrays. Order: structural, then constraints, then feature transforms, then dtype, then concatenate and rename. Details: `references/simulators-and-adapters.md`.
3. Budget. Time `simulator.sample(batch_size)`. Cheap simulators train online (`fit_online`, fresh data every step, Adam). Expensive ones pre-simulate (`fit_offline`, AdamW with weight decay), and data too large for RAM stream from files (`fit_disk`).
4. Train with validation data, then read `bf.diagnostics.loss(history)`. Details: `references/approximators-and-training.md`.
5. In-silico validation on fresh simulations: recovery, SBC ECDF with `difference=True`, coverage, z-score versus contraction, and `compute_default_diagnostics`. Check recovery across the range of every context variable (N, T, design).
6. Real data. Check that the observed summaries sit inside the training distribution, then sample, then run posterior predictive checks by re-simulating posterior draws. A network that passes step 5 and fails step 6 points to simulator misspecification, which more training does not fix. Details: `references/diagnostics-and-debugging.md`.

## Rules that prevent silent failure

- Never pass `adapter=` together with `inference_variables=` / `summary_variables=` / `inference_conditions=` to a workflow. The source does `adapter = adapter or default_adapter(...)`, so the naming kwargs are silently discarded.
- `Adapter.standardize` in 2.0.14 requires explicit `mean=` and `std=`. Learned running standardization belongs to the approximator: `standardize="inference_variables"` (default), `"all"`, a list of routing keys, or `None` (use `None` when the adapter already log-transforms or scales everything).
- Constrain bounded parameters (`.constrain("sigma", lower=0)`, `lower=0, upper=1`) before concatenation. The inverse transform guarantees support in posterior draws.
- `.concatenate` order defines the column order of `inference_variables`. Diagnostics and `split=True` follow it.
- `.group(...)` (nested dicts for `FusionNetwork`) must be the last adapter step, because most transforms cannot handle nested structures.
- Each `fit_*` call builds a fresh cosine schedule with 5 percent warmup over that call's epochs and discards the optimizer unless `keep_optimizer=True`. A second `fit_*` call restarts the warmup and learning rate schedule.
- `ConsistencyModel(total_steps=...)` must equal `epochs * num_batches` exactly. `StableConsistencyModel` has no such requirement.
- `save_best_only=True` picks noise for noisy losses (flow matching, diffusion, consistency). Keep the default.
- Save the full approximator (`approximator.save("x.keras")`). The `.keras` file carries the adapter. Weights-only files need an identical rebuilt architecture. Load with `import bayesflow` first, then `keras.saving.load_model(...)` or `workflow.load_approximator(path=...)`. Check a few outputs after every load.
- A shared summary network across ensemble members logs a deserialization warning. Clone it per member when the ensemble must be saved.

## Doc versus source (2.0.14)

The installed library is authoritative where the user guide disagrees:

- `DiffusionModel` defaults are `noise_schedule="cosine"`, `prediction_type="velocity"`, `loss_type="noise"`. The guide table says `"edm"` and `"F"`.
- `FlowMatching(time_power_law_alpha=0.5)` is the default. The guide says 0.0.
- `SetTransformer` and `TimeSeriesTransformer` default to two blocks, `embed_dims=(64, 64)`. The guide's "Base" size is three blocks.
- `ModelComparisonWorkflow(standardize="all")` is its default, unlike `BasicWorkflow` (`"inference_variables"`).
- `ConsistencyModel` takes `sigma2`, `max_time`, `s0`, `s1`, `eps`. Its latent std equals `max_time`.
- Several example notebooks state priors or sizes in the prose that differ from the code beside them. Trust the code.

## References

| Read when | File |
|---|---|
| Writing simulators, `meta_fn`, batching, rejection sampling, any adapter transform | `references/simulators-and-adapters.md` |
| Choosing or sizing summary and inference networks, custom networks | `references/networks.md` |
| Approximator classes, workflows, datasets, training strategy, saving, PyMC bridge, custom torch loops | `references/approximators-and-training.md` |
| Diagnostics, SBC, reading loss curves, misspecification, debugging bad posteriors | `references/diagnostics-and-debugging.md` |
| Finding an official example that matches the problem | `references/examples.md` |
