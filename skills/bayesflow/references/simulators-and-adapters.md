# Simulators and adapters

## Simulators

`bf.make_simulator` dispatches on its argument:

- A list of functions builds a `SequentialSimulator`. Each function returns a dict. Its arguments are filled by name from the keys produced so far, so `likelihood(mu, sigma)` receives the prior's `mu` and `sigma`. A function that does not use every upstream key takes `**kwargs`. Context defaults work as plain keyword defaults (`def likelihood(mu, n=30)`).
- A single function builds a `LambdaSimulator`. `bf.simulators.LambdaSimulator(fn, is_batched=True)` calls `fn(batch_shape)` once per batch, which is much faster when the simulator vectorizes.
- `meta_fn=` returns context drawn once per batch (sample size N, horizon T, design). Every row in that batch shares the value, which keeps the batch rectangular. It comes back as an unbatched scalar, so route it with `.broadcast("N", to="<batched key>")` before using it as a condition.
- Any object with `sample(batch_shape) -> dict` works as a simulator, including a hand-written class that handles an `int` or tuple batch shape.

Shapes from `simulator.sample(B)`: scalars become `(B, 1)`, vectors `(B, d)`, matrices `(B, n, d)`. Outputs whose length varies across rows within one batch cannot be stacked. Pad them, or move the varying size into `meta_fn`.

Other methods:

- `simulator.sample(B, **kwargs)` forwards keyword arguments to the functions. Built-in simulators accept fixed parameters this way (`simulator.sample(1, parameters=draw)`), which is the re-simulation path for posterior predictive checks.
- `SequentialSimulator.sample_parallel(B, n_jobs=-1, seed=None, **kwargs)` runs the functions through joblib for expensive simulators.
- `simulator.rejection_sample(B, predicate=fn, sample_size=...)` keeps rows where `predicate(data)` is true. It returns at least B rows and usually overshoots, so trim when a fixed count matters. A predicate that rejects almost everything never terminates.
- `simulator.simulators[0].sample(1000)` draws from the prior stage alone for prior plots.
- `bf.simulators.ModelComparisonSimulator(simulators=[sim0, sim1], p=None, use_mixed_batches=True, shared_simulator=None)` adds a one-hot `model_indices` key. `shared_simulator` supplies context shared across models. Key conflicts between models default to `key_conflicts="drop"`.
- Built-in benchmarks: `TwoMoons`, `SIR`, `LotkaVolterra`, `SLCP`, `SLCPDistractors`, `GaussianLinear`, `GaussianLinearUniform`, `GaussianMixture`, `BernoulliGLM`, `BernoulliGLMRaw`, `InverseKinematics`, plus `HierarchicalSimulator`.

Simulator design rules:

- Use a module-level `np.random.default_rng(seed)` inside the functions, so a seed set once controls the run.
- Move any reduction to observation times into the simulator, as when porting from ABC. The network sees exactly what the observed data will look like.
- Clip or rescale pathological outputs inside the simulator (extreme tails, near-infinite variance regions, values spanning orders of magnitude). A few huge simulations cause NaN or exploding losses.
- When numba compiles the simulator, warm every branch once before training (for example both `nu=np.inf` and finite `nu`), so compilation does not stall the data loader.
- Under JAX, data whose shape changes across batches (a varying N) recompiles the training step during the first steps. Expect slow early epochs.

## Adapter

The adapter is an ordered, mostly invertible pipeline applied identically during training and inference. `print(adapter)` shows the steps. `adapter(data)` runs it forward and `adapter(data, inverse=True)` runs it backward. Sampling applies the inverse automatically, so posterior draws come back on the original scale under the original names.

### Transforms (2.0.14 signatures)

| Method | Purpose |
|---|---|
| `broadcast(keys, to=, expand="left", exclude=-1, squeeze=None)` | Replicate a batch-shared value (from `meta_fn`) to the batch size of `to`. `to` must also be present at inference time |
| `as_set(keys)` | Mark exchangeable observations and add a trailing feature axis, `(B, N)` to `(B, N, 1)` |
| `as_time_series(keys)` | Same shape effect for ordered sequences |
| `constrain(keys, lower=, upper=, method="default", inclusive="both", epsilon=1e-15)` | Bijection to unconstrained space. Lower or upper only uses `softplus` (or `exp`). Both bounds use `sigmoid` (or `expit`) |
| `log(keys, p1=False)` | Log, or log1p with `p1=True` for non-negative counts |
| `sqrt(keys)` | Compress the range of context variables such as N |
| `scale(keys, by=)`, `shift(keys, by=)` | Fixed affine maps |
| `standardize(include=None, mean=, std=)` | Fixed standardization. `mean` and `std` are required |
| `nan_to_num(keys, default_value=0.0, return_mask=False, mask_prefix="mask")` | Replace NaN and optionally emit a mask key for missing data |
| `one_hot(keys, num_classes=)` | Categorical inputs |
| `convert_dtype("float64", "float32")` | Required near the end |
| `concatenate(keys, into=, axis=-1)` | Stack along the last axis. The list order is the column order |
| `rename(from_key, to_key)` | Route a key |
| `drop(keys)`, `keep(keys)` | Remove keys or keep only the listed ones |
| `split(key, into=, indices_or_sections=, axis=-1)`, `take(include, indices=, axis=-1)` | Slice arrays |
| `expand_dims(keys, axis=)`, `squeeze(keys, axis=)`, `to_array()` | Shape and type fixes. `to_array()` converts list or scalar outputs to arrays |
| `random_subsample(key, sample_size=, axis=-1)` | Random subsets of a set axis, an augmentation for varying N |
| `group(keys, into=, prefix="")` | Nest keys into a dict, for `FusionNetwork`. Must come last |

### Ordering

1. Structural: `broadcast`, `as_set`, `as_time_series`.
2. Constraints: `constrain`.
3. Feature transforms: `log`, `sqrt`, `scale`, `standardize`.
4. `convert_dtype("float64", "float32")`.
5. Assembly: `concatenate`, `rename`, then `group` last if used.

Constrain before concatenating, because constraints are per key. Broadcast before anything treats the value as per-row.

### Default adapters

- `BasicWorkflow(inference_variables=..., summary_variables=..., inference_conditions=...)` builds an adapter that converts float64 to float32 and concatenates each role. It does not add a feature axis, so summary variables must already be 3-D. Use it only for plain renames.
- `Approximator.build_adapter(inference_variables=, inference_conditions=, summary_variables=, sample_weight=, ...)` (on `ContinuousApproximator`, `RatioApproximator` and the others) runs `to_array`, dtype conversion and concatenation, applies `as_set` to the summary variables, and ends with a `keep` of the routing keys. The two defaults differ, so check the shape of `adapter(sample)` either way.
- `bf.Adapter.create_default(inference_variables)` is `to_array`, dtype conversion and concatenation of the target. Further steps chain onto it.

### Recipes

Varying-N set data with a positive scale:

```python
adapter = (
    bf.Adapter()
    .broadcast("N", to="x")
    .as_set(["x", "y"])
    .constrain("sigma", lower=0)
    .sqrt("N")
    .convert_dtype("float64", "float32")
    .concatenate(["beta", "sigma"], into="inference_variables")
    .concatenate(["x", "y"], into="summary_variables")
    .rename("N", "inference_conditions")
)
```

Count time series with positive parameters, log-transformed so learned standardization is unnecessary (pair with `standardize=None` on the workflow):

```python
adapter = (
    bf.Adapter()
    .convert_dtype("float64", "float32")
    .as_time_series("cases")
    .concatenate(["lambd", "mu", "D", "I0", "psi"], into="inference_variables")
    .rename("cases", "summary_variables")
    .log(["inference_variables", "summary_variables"], p1=True)
)
```

Hand-crafted statistics as direct conditions, raw series dropped:

```python
adapter = (
    bf.Adapter()
    .convert_dtype("float64", "float32")
    .drop(["x", "y", "t"])
    .concatenate(["alpha", "beta", "gamma", "delta"], into="inference_variables")
    .concatenate(["means", "log_vars", "auto_corrs", "cross_corr"], into="inference_conditions")
)
```

Two modalities for a `FusionNetwork` whose backbone keys are `input_a` and `input_b`:

```python
adapter = (
    bf.Adapter.create_default(["mu", "sigma"])
    .rename("observables_a", "input_a")
    .concatenate(["observables_b", "time_b"], into="input_b")
    .group(["input_a", "input_b"], into="summary_variables")
)
```

NLE (data as target, parameters as conditions):

```python
adapter = (
    bf.Adapter()
    .convert_dtype("float64", "float32")
    .concatenate(["theta_1", "theta_2"], into="inference_conditions")
    .rename("x", "inference_variables")
)
```

Image-shaped targets need image-shaped conditions. Tile scalar parameters to `(H, W, n_params)` in the simulator and route that array to `inference_conditions`. Images always carry an explicit channel axis, `(H, W, C)`.

### Feature engineering inside the pipeline

The summary network only sees what the adapter gives it. Raw values spanning orders of magnitude, heavy tails, or per-set statistics the network would struggle to compute (variance of a few hundred points, quantiles, regression fits) are worth computing in the simulator and passing as extra feature columns or as `inference_conditions`. Learned summaries usually beat hand-crafted ones when architecture and training budget are adequate. Hand-crafted ones are the fast way to iterate and a useful baseline.

Conditions at inference time use the raw, pre-adapter key names. Passing a full simulated dict as `conditions` is fine, because the parameter keys in it are not routed to the conditions. A raw observed array needs its batch axis (`obs[None, :]`) and the same per-row layout as the simulator output.
