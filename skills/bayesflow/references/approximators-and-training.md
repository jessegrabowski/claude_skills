# Approximators, workflows and training

## Contents

- Workflows versus approximators
- Training strategies and datasets
- Optimizer defaults
- Querying a trained approximator
- Specialized approximators
- Saving and loading
- PyMC bridge (NLE and NRE)
- Custom training loops

## Workflows versus approximators

A workflow wraps an approximator and supplies the default adapter, the optimizer, checkpointing and diagnostics. The approximator is always reachable at `workflow.approximator`, and every query method works on it directly.

```python
bf.BasicWorkflow(simulator=None,
                 adapter=None,
                 inference_network="coupling_flow",
                 summary_network=None,
                 initial_learning_rate=5e-4,
                 optimizer=None,
                 checkpoint_filepath=None,
                 checkpoint_name="model",
                 save_weights_only=False,
                 save_best_only=False,
                 restore=False,
                 inference_variables=None,
                 inference_conditions=None,
                 summary_variables=None,
                 standardize="inference_variables")
```

- Passing a `ScoringRuleNetwork` as `inference_network` makes the workflow build a `ScoringRuleApproximator`. Any other network gives a `ContinuousApproximator`.
- `inference_variables=` is what the automatic diagnostics use to find targets. With a custom adapter, the diagnostics work on whatever keys come back from `sample`.
- `standardize` accepts `"all"`, `None`, or a subset of `["inference_variables", "summary_variables", "inference_conditions"]`. The approximator learns running statistics, and the inverse is applied to draws.

The direct approximator path:

```python
approximator = bf.ContinuousApproximator(inference_network=bf.networks.FlowMatching(),
                                         summary_network=bf.networks.SetTransformer(summary_dim=10),
                                         adapter=adapter,
                                         standardize="inference_variables")
approximator.compile(optimizer=keras.optimizers.AdamW(learning_rate=1e-4, clipnorm=1.1))
history = approximator.fit(simulator=simulator,
                           epochs=50,
                           num_batches=200,
                           batch_size=64)
```

`approximator.compile` is required before `approximator.fit`. `approximator.fit` takes `num_batches=` while `workflow.fit_online` takes `num_batches_per_epoch=`. `approximator.fit(simulator=...)` builds an `OnlineDataset` with `workers="auto"` (all CPUs, threads by default) and `batch_size="auto"` when omitted. Pass `dataset=` instead of `simulator=` for pre-built datasets. All other keyword arguments go to `keras.Model.fit` (`callbacks`, `verbose`, `validation_data`, `initial_epoch`).

## Training strategies and datasets

| Situation | Call | Dataset class |
|---|---|---|
| Simulator cheap enough to call every step | `workflow.fit_online(epochs=100, num_batches_per_epoch=100, batch_size=32, validation_data=None)` | `OnlineDataset` |
| Pre-simulated data fits in RAM | `workflow.fit_offline(data=dict, epochs=100, batch_size=32, validation_data=None)` | `OfflineDataset` |
| Pre-simulated data on disk | `workflow.fit_disk(root=, pattern="*.pkl", load_fn=None, batch_size=32, epochs=100)` | `DiskDataset` |
| Disk-backed validation, batch inspection, ensembles | build datasets and call `workflow.approximator.fit(dataset=..., validation_data=...)` | explicit |

- `validation_data` takes a dict of arrays, or an int that makes the workflow simulate that many validation sets (needs a simulator). Always supply it. Without it the loss plot shows no generalization gap.
- `augmentations=` (a callable or a dict of callables) runs on each training batch before the adapter. Use it for noise injection or random subsampling during training only.
- Online training never sees the same simulation twice, so it cannot overfit the simulation pool. Offline training reuses a fixed pool and can overfit when the pool is small relative to network capacity.
- Online timing is bounded by the simulator. Time `simulator.sample(batch_size)` first. A simulator that needs about 10 ms per batch of 32 runs fine online. Slow ones should be pre-simulated in parallel (`sample_parallel`) and trained offline.
- For `DiskDataset`, `load_fn(path)` receives one matched file and returns one complete sample dict. Test it on one file before training. Pickled dicts per sample are the low-overhead format.

Explicit datasets:

```python
train_dataset = bf.OnlineDataset(simulator=simulator,
                                 batch_size=64,
                                 num_batches=100,
                                 adapter=adapter)
val_dataset = bf.OfflineDataset(data=validation_data,
                                batch_size=64,
                                adapter=adapter,
                                shuffle=False)
batch = train_dataset[0]
```

`train_dataset[0]` returns one adapted batch, the quickest check of routed shapes and dtypes.

## Optimizer defaults

When no optimizer is passed, each `fit_*` call builds one sized to that call:

- The schedule is `CosineDecay` with linear warmup over the first 5 percent of steps from `0.1 * initial_learning_rate` to `initial_learning_rate`, decaying to 0 at `epochs * num_batches`.
- Online training uses `Adam(clipnorm=1.5)`. Offline and disk training use `AdamW(weight_decay=5e-3, clipnorm=1.5)`.
- The optimizer is discarded after the call unless `keep_optimizer=True`. A second `fit_*` call therefore restarts warmup and decay. Train in one call with the full epoch count, or pass `keep_optimizer=True` and accept that the decayed schedule continues.
- A custom `optimizer=` on the workflow or `approximator.compile(optimizer=...)` replaces all of this. Size a custom `CosineDecay` with `decay_steps = epochs * num_batches`.

The examples use `initial_learning_rate` 5e-4 by default, 1e-3 for model comparison, and 1e-4 for image diffusion.

## Querying a trained approximator

- `sample(num_samples=, conditions=, split=False, batch_size=None, seed=None)` returns `{name: (num_datasets, num_samples, dim)}`. `batch_size` chunks the datasets to bound memory. `split=True` splits a concatenated key back into one array per column. Generative samplers (flow matching, diffusion) are slow, so subsample conditions for diagnostics and raise `batch_size` on GPU.
- `log_prob(data=)` returns `(num_datasets,)` for networks with exact density.
- `estimate(conditions=)` returns point estimates for scoring-rule approximators and model probabilities for model comparison.
- `workflow.simulate(n)` draws fresh test sets. `workflow.samples_to_data_frame(samples)` flattens draws to a DataFrame.
- `approximator.sample(..., return_summaries=True)` also returns the summary network outputs, which are useful for out-of-distribution checks.

## Specialized approximators

### Model comparison

```python
workflow = bf.ModelComparisonWorkflow(simulator=[simulator_0, simulator_1],
                                      summary_variables="x",
                                      summary_network=bf.networks.SetTransformer(),
                                      scoring_rules="cross_entropy",
                                      model_names=["M0", "M1"],
                                      initial_learning_rate=1e-3)
history = workflow.fit_online(epochs=50,
                              num_batches_per_epoch=50,
                              batch_size=128)
estimates = workflow.estimate(conditions=test_data)
```

- A list of simulators is wrapped in a `ModelComparisonSimulator` with uniform model priors. The targets are the auto-named `model_indices`.
- PMP rules (`"cross_entropy"` default, `"brier"`, `"polynomial"`) output softmax probabilities, and `estimate` returns `model_probs` and `logits`. Bayes factor rules (`"exponential"`, `"logistic"`) output log Bayes factors relative to model 0, and `estimate` returns `model_probs` and `log_bayes_factors`. The reported log odds equal log Bayes factors only under uniform model priors.
- A list of rules trains one head per rule on a shared summary network and pools them by a log opinion pool.
- Prefer PMP rules when Bayes factors can be extreme (nested models, long series). The exponential loss is dominated by a few extreme datasets.
- `standardize="all"` is this workflow's default.

### Ratio estimation (contrastive NRE)

`bf.RatioApproximator(inference_network=bf.networks.MLP(), adapter=adapter, K=5, gamma=1.0, standardize="inference_variables")` learns `log p(x given theta) - log p(x)`. Route parameters to `inference_variables` and data to `inference_conditions`, the NPE layout. Set `K`, the number of contrastive candidates, near `batch_size / 2`. The examples used `K=64` with batch 128 and `K=32` with batch 64. `log_ratio(data=)` evaluates the learned log ratio. Check it against an analytic log likelihood where one exists: `LL - log_ratio` should be constant over theta.

### Autoregressive (joint trajectories)

```python
approximator = bf.AutoregressiveApproximator(inference_network=bf.networks.CouplingFlow(),
                                             encoder_network=bf.networks.RecurrentNetwork(return_sequences=True),
                                             decoder_network=bf.networks.RecurrentDecoder(),
                                             adapter=adapter,
                                             standardize="all")
```

The encoder must return one encoding per time step (`return_sequences=True`). `TimeSeriesTransformer(return_sequences=True)` and `TransformerDecoder()` are the alternatives. Training uses teacher forcing, and sampling feeds the decoder its own past draws. Draws have shape `(num_datasets, num_samples, T, dim)`.

### Compositional (many datasets sharing global parameters)

`CompositionalWorkflow` requires a `DiffusionModel`. Train on small blocks (for example 5 subjects), validate calibration at that scale, then compose:

```python
posterior = workflow.compositional_sample(num_samples=100,
                                          conditions={"sim_data": x},
                                          compute_prior_score=prior_score,
                                          method="two_step_adaptive",
                                          steps="adaptive",
                                          mini_batch_size=10,
                                          return_summaries=True,
                                          summaries=None)
summaries = posterior.pop("_summaries")
```

- Conditions are shaped `(n_datasets, n_compositional, ...)`, with the composition axis second.
- `compute_prior_score(x)` maps a dict keyed by the pre-adapter parameter names to the prior score per key (`-(x - m) / s**2` for a Gaussian prior). Key-name mismatches here are a known failure in the official example. Keep one prior-hyperparameter dict and use it in both the simulator and the score.
- Reuse `summaries` across sampler settings, because summarizing thousands of datasets dominates cost.
- `compositional_bridge_d0` and `compositional_bridge_d1` damp accumulated score error. `use_jac=True` with a diffused-prior score that takes `time` improves calibration for fewer than about 50 compositions.
- `CompositionalWorkflow.from_basic_workflow(trained_basic_workflow)` promotes a trained diffusion workflow without retraining.
- Local parameters come from a second workflow trained with the global parameters as `inference_conditions`, then `ancestral_sample(conditions=..., ancestral_conditions=global_posterior)`.

### Ensembles

```python
workflow = bf.EnsembleWorkflow(simulator=simulator,
                               adapter=adapter,
                               inference_networks={"flow": bf.networks.FlowMatching(),
                                                   "coupling": bf.networks.CouplingFlow()},
                               summary_networks={"flow": bf.networks.SetTransformer(),
                                                 "coupling": bf.networks.SetTransformer()})
history = workflow.fit_online(epochs=50,
                              num_batches_per_epoch=100,
                              batch_size=64,
                              data_reuse=0.5)
```

- A single network with `ensemble_size=n` is cloned into independent members unless `share_inference_network=True`. A single summary network is shared, which logs a warning that shared components may not deserialize. Give each member its own instance when the ensemble will be saved.
- `data_reuse` sets the overlap of member training data (1.0 means identical data).
- `sample(..., merge_members=False)` returns per-member dicts. `member_weights={...}` sets mixture weights. Point-estimate members are excluded from `sample` and `log_prob`.
- `estimate(conditions=, groupby="variable")` nests variable, estimate and member.

## Saving and loading

- Checkpoint during training with `checkpoint_filepath=` and `checkpoint_name=` on the workflow. It saves `{name}.keras` every epoch, monitoring `val_loss` when validation data exists.
- `workflow.approximator.save("path/model.keras")` saves the architecture, weights and adapter. The parent directory must exist.
- `workflow.load_approximator(path=...)` handles `.keras` and `.weights.h5`. `restore=True` on the constructor loads the checkpoint immediately.
- `import bayesflow` and then `keras.saving.load_model("path/model.keras")` works without a workflow. Assign the result to `workflow.approximator` to regain the workflow helpers.
- Weights-only files (`save_weights_only=True`) need the identical architecture built first and risk adapter mismatches.
- Custom networks need `@serializable` and `get_config` (see `networks.md`).
- After every load, compare output shapes and a few draws against values recorded before saving.

## PyMC bridge (NLE and NRE)

```python
from bayesflow.wrappers.pymc import NeuralDistribution

neural_likelihood = NeuralDistribution(workflow.approximator,
                                       param_names=["g", "k", "rho"],
                                       exchangeable=True)

with pm.Model():
    g = pm.Uniform("g", lower=-1.0, upper=1.0)
    k = pm.Uniform("k", lower=0.0, upper=0.5)
    rho = pm.Uniform("rho", lower=-0.9, upper=0.9)
    neural_likelihood("obs", g=g, k=k, rho=rho, observed=observed_data.astype("float32"))
```

- It accepts a `ContinuousApproximator` trained in NLE mode (data as `inference_variables`, parameters as `inference_conditions`, one observation per simulation) or a `RatioApproximator`.
- `param_names` sets the order in which parameters reach the network and must match the training `inference_conditions` (NLE) or `inference_variables` (NRE) order.
- `exchangeable=True` vmaps the network over the first axis of `observed` and PyMC sums the per-trial values. Per-trial parameter vectors (a regression `mu = b0 + b1 * x`) work without retraining.
- The JAX backend registers an exact VJP, so NUTS works.
- Construction sets `pytensor.config.floatX` to float32 for the whole process.
- Keep PyMC priors inside the training prior's support. The network extrapolates arbitrarily outside it.
- Pass explicit `initvals` inside the trained region.
- The examples use `cores=1`, or a spawn multiprocessing context, because forking a process that has initialized JAX hangs or dies on Linux.
- `simulator_fn=(rng, *params, size) -> ndarray` enables prior and posterior predictive sampling through PyMC.
- The resulting posterior mixes epistemic uncertainty with surrogate error. Validate it with SBC as for any other surrogate.

## Custom training loops

Inference networks are plain Keras layers. On the torch backend they can be trained by hand, for example jointly with experimental designs:

```python
posterior_net = bf.networks.CouplingFlow()
posterior_net.build(xz_shape=(32, num_parameters), conditions_shape=(32, num_conditions))

with torch.enable_grad():
    optimizer = torch.optim.AdamW(list(posterior_net.parameters()) + list(simulator.parameters()), lr=1e-3)
    for step in range(5000):
        optimizer.zero_grad()
        theta, y = simulator(batch_shape=(128,))
        loss = -posterior_net.log_prob(theta, conditions=y).mean()
        loss.backward()
        optimizer.step()
```

`torch.enable_grad()` is mandatory because importing bayesflow under torch disables autograd globally. Scale conditions to roughly unit range by hand, since no adapter or standardization runs in this path. `posterior_net.sample(n, conditions=...)` needs one condition row per draw.
