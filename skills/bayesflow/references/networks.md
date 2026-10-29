# Networks

All networks live in `bf.networks`. Pass instances to approximators or workflows. Workflows also accept registered names: `"coupling_flow"`, `"flow_matching"`, `"diffusion_model"`, `"consistency_model"` for inference networks, and `"deep_set"`, `"set_transformer"`, `"time_series_transformer"`, `"time_series_network"`, `"fusion_transformer"` for summary networks. Base distributions accept `"normal"`, `"student"` and `"mixture"`. Defaults below come from 2.0.14 `inspect.signature` and override the user guide where they differ.

## Summary networks

| Network | Input | Use |
|---|---|---|
| `SetTransformer` | `(B, N, D)` | Exchangeable observations. Permutation invariant |
| `DeepSet` | `(B, N, D)` | Cheaper set baseline with fewer interactions |
| `TimeSeriesTransformer` | `(B, T, D)` | Default for ordered sequences. Time2Vec embedding |
| `TimeSeriesNetwork` | `(B, T, D)` | Conv1D plus bidirectional GRU. Faster, less expressive |
| `FusionTransformer` | `(B, T, D)` | Attention plus a recurrent template for complex temporal structure. Slower |
| `ConvolutionalNetwork` | `(B, H, W, C)` | Images and spatial fields. ResNet-style |
| `FusionNetwork(backbones={...}, head=...)` | dict of inputs | Several modalities. Backbone keys must match the adapter's `group` keys. The head sees the concatenated backbone outputs |
| `RecurrentNetwork` | `(B, T, D)` | Encoder for `AutoregressiveApproximator` with `return_sequences=True` |

Never use `SetTransformer` on ordered data, because it discards order.

### Defaults and sizing

- `SetTransformer(summary_dim=16, embed_dims=(64, 64), num_heads=(4, 4), num_seeds=4, dropout=0.05, num_inducing_points=None, ...)`. The tuple length sets the number of attention blocks, and `embed_dims` and `num_heads` must have equal length. Raise `num_seeds` for richer pooling. `num_inducing_points` bounds attention cost for large N.
- `DeepSet(summary_dim=16, embed_dim=64, depth=2, mlp_widths=(64,), inner_pooling="mean", dropout=0.05, ...)`.
- `TimeSeriesTransformer(summary_dim=16, embed_dims=(64, 64), num_heads=(4, 4), time_embed_dim=8, time_axis=None, downsample=None, return_sequences=False, dropout=0.05, ...)`. Set `time_axis=-1` only when the last feature column holds actual observation times (irregular sampling). Pointing it at a data channel degrades the fit. With `time_axis=None` uniform spacing is assumed.
- `TimeSeriesNetwork(summary_dim=16, filters=32, kernel_sizes=3, strides=1, recurrent_type="gru", recurrent_dim=128, bidirectional=True, skip_steps=4, dropout=0.05)`.
- `ConvolutionalNetwork(summary_dim=, widths=, blocks_per_stage=, down_mode=, pool_head=, norm=, groups=)`. One example uses `widths=(8, 16, 32, 64), blocks_per_stage=1, down_mode="max_pool", pool_head="flatten", norm="group", groups=1`.

Guide size ladder, to be climbed only when diagnostics show poor recovery after adequate training and no overfitting:

| Size | Transformers `embed_dims` / `num_heads` | `TimeSeriesNetwork` `filters` / `recurrent_dim` | `ConvolutionalNetwork` `widths` |
|---|---|---|---|
| Small | `(32, 32)` / `(2, 2)` | `(16, 32)` / 64 | `(16, 32)` |
| Base | `(64, 64, 64)` / `(4, 4, 4)` | `(32, 64)` / 128 | `(32, 64, 128)` |
| Large | `(128,)*4` / `(8,)*4` | `(32, 64, 128)` / 256 | `(32, 64, 128, 256)` |
| XL | `(256,)*5` / `(16,)*5` | `(64, 128, 256)` / 512 | `(32, 64, 128, 256, 512)` |

`summary_dim` starts near 3 times the number of parameters and never goes below the number of parameters. Oversized networks train slower and can hurt calibration on simple problems.

### Custom summary networks

Subclass `bf.networks.SummaryNetwork`, decorate with `@serializable("<project>.networks")` from `bayesflow.utils.serialization`, and return the constructor arguments from `get_config`. Without both, `.save` and `load_model` fail.

```python
import keras

from bayesflow.utils.serialization import serializable, serialize


@serializable("my_project.networks")
class GRUSummary(bf.networks.SummaryNetwork):
    def __init__(self, summary_dim=8, units=64, **kwargs):
        super().__init__(**kwargs)
        self.summary_dim = summary_dim
        self.units = units
        self.gru = keras.layers.GRU(units)
        self.dense = keras.layers.Dense(summary_dim)

    def call(self, time_series, training=False, **kwargs):
        return self.dense(self.gru(time_series, training=training))

    def get_config(self):
        base = super().get_config()
        return base | serialize({"summary_dim": self.summary_dim, "units": self.units})
```

Call `serialize` on any constructor value that is itself a Keras or BayesFlow object. A pretrained Keras Hub backbone can sit inside such a wrapper with `backbone.trainable = False` and a trainable projection head.

## Inference networks

| Network | Sampling cost | Exact density | Use |
|---|---|---|---|
| `CouplingFlow` | 1 pass | yes | Simple to moderate posteriors, fast sampling, `log_prob` |
| `FlowMatching` | ODE, 10 to 50 passes | yes | Complex and multimodal posteriors |
| `DiffusionModel` | SDE or ODE, many passes | yes | Most flexible. Required for composition, guidance and masked conditionals |
| `ConsistencyModel` | 1 to few passes | no | Fast sampling, hard to tune |
| `StableConsistencyModel` | 1 to few passes | no | Consistency model without `total_steps` |
| `ScoringRuleNetwork` | 1 pass | parametric only | Point estimates, quantiles, MVN |
| `PointNetwork` | 1 pass | no | Mean and quantiles shorthand |

### CouplingFlow

`CouplingFlow(subnet="mlp", depth=6, transform="affine", permutation="random", use_actnorm=True, base_distribution="normal", subnet_kwargs=None, transform_kwargs=None)`.

- `transform="spline"` is more expressive and beats affine on low-dimensional multimodal posteriors. It is the usual choice for NLE.
- `base_distribution="student"` or `bf.distributions.DiagonalStudentT(df=...)` handles heavy tails.
- `subnet_kwargs={"widths": [256, 256, 256], "dropout": 0.05}` widens the coupling MLPs.
- Its negative log likelihood loss is a direct quality signal.

### FlowMatching

`FlowMatching(subnet="time_mlp", base_distribution="normal", use_optimal_transport=False, loss_fn="mse", integrate_kwargs=None, optimal_transport_kwargs=None, subnet_kwargs=None, time_power_law_alpha=0.5, fixed_target_prob=0.0, missing_target_prob=0.0, missing_conditions_prob=0.0)`.

- After the initial drop, the MSE loss stops tracking quality. Judge it by recovery and calibration.
- `use_optimal_transport=True` costs about 2.5 times more per step and often converges in fewer steps.
- `integrate_kwargs={"steps": 20}` trades accuracy for sampling speed and can also be passed to `.sample()`.
- It improves with long training (the Lotka-Volterra example used 50 epochs where a point network needed 15).

### DiffusionModel

`DiffusionModel(subnet="time_mlp", noise_schedule="cosine", prediction_type="velocity", loss_type="noise", subnet_kwargs=None, schedule_kwargs=None, integrate_kwargs=None, fixed_target_prob=0.0, missing_target_prob=0.0, missing_conditions_prob=0.0)`.

- `noise_schedule` is `"cosine"` or `"edm"`. `prediction_type` is one of `"velocity"`, `"noise"`, `"F"`, `"x"`, `"score"`, `"potential"`.
- Sampling-time options passed to `sample()`:
  - `stop_time=t` stops denoising early.
  - `guidance_kwargs=dict(constraints=[c_fn], guidance_strength=lam)` steers samples toward `c_fn(z) <= 0`, where `c_fn` uses `keras.ops`.
  - Masked conditionals need training with `subnet="diffusion_transformer"` and nonzero `fixed_target_prob`, `missing_target_prob`, `missing_conditions_prob`. Then pass `observed_condition_mask` (1 present, 0 missing), `infer_target_mask` (1 inferred, 0 marginalized, and the returned value at 0 positions is latent noise to discard), or `fixed_target_mask` with `fixed_target_value` (0 means fixed at the given value).
- On JAX, sampling logs "JAX backend needs to preallocate random samples for 'max_steps=1000'". It is informational.
- Image targets take `subnet=bf.networks.UNet` (default start), `UViT`, or `ResidualUViT` (hardest problems), passed as a class with `subnet_kwargs`. The examples use `prediction_type="velocity"`, `noise_schedule="cosine"`, `initial_learning_rate=1e-4`, and a GPU.

### Consistency models

`ConsistencyModel(total_steps, subnet="time_mlp", max_time=80, sigma2=1.0, eps=0.001, s0=10, s1=150, ...)`.

- `total_steps` must equal `epochs * num_batches`.
- `max_time` is also the latent std and must exceed the target's std. Values from 10 to 200 work, and a new problem usually needs tuning.
- `s0=10` works. A high `s1` sometimes breaks training.
- Leave `sigma2=1.0` when targets are standardized. Leave `eps` alone.
- Use `subnet_kwargs={"dropout": 0.0}`, because dropout hurts consistency models.
- The consistency loss says little on its own.

`StableConsistencyModel(subnet="time_mlp", sigma=1.0, steps=15, subnet_kwargs=None, weight_mlp_kwargs=None, ...)` needs no `total_steps` and is the easier drop-in.

### Point estimation

```python
from bayesflow.scoring_rules import MeanScore, MvNormalScore, QuantileScore

inference_network = bf.networks.ScoringRuleNetwork(
    scoring_rules={"mean": MeanScore(),
                   "quantiles": QuantileScore(q=[0.1, 0.5, 0.9]),
                   "mvn": MvNormalScore()}
)
inference_network = bf.networks.PointNetwork(["mean", "quantiles"],
                                             q=[0.05, 0.25, 0.5, 0.75, 0.95])
```

`estimate(conditions=...)` returns `{variable: {rule: array}}` by default (`groupby="variable"`). Means are `(B, dim)` and quantiles `(B, n_q, dim)`, with the quantile axis before the variable axis. A custom rule subclasses `ScoringRule` as a negatively oriented proper scoring rule. Point networks need one forward pass and suit rapid iteration on simulator and summary design. A normal fitted to their quantiles ignores correlation and multimodality.

### Other building blocks

`MLP(widths=...)` is the classifier backbone for model comparison and ratio estimation. `TimeMLP` backs the generative networks. `RecurrentDecoder` and `TransformerDecoder` are the autoregressive decoders. `DiffusionTransformer`, `UNet`, `UViT` and `ResidualUViT` are subnets.
