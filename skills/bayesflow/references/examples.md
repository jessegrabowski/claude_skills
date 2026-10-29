# Official examples (v2.0.14)

Each notebook is at `https://bayesflow.org/v2.0.14/_examples/<Name>.html` and in the repository under `examples/<Name>.ipynb`. Several have prose that disagrees with the code beside them (prior ranges, sizes, scoring rule named). The code is what ran.

| Example | Pattern | Key APIs |
|---|---|---|
| Two_Moons_Starter | Bimodal posterior, comparison of inference networks on identical offline data | `FlowMatching(subnet_kwargs={"widths": (256,)*6, "dropout": 0.0})`, `ConsistencyModel(total_steps=..., max_time=10)`, spline `CouplingFlow`, `fit_offline` |
| Linear_Regression_Starter | Varying N through `meta_fn`, set summaries, positive scale, SBC with custom test quantities, save and load | `broadcast`, `as_set`, `constrain`, `sqrt`, `SetTransformer(summary_dim=10)`, `standardize=["inference_variables", "summary_variables"]`, `calibration_ecdf(test_quantities=...)` |
| One_Sample_TTest | Two-model comparison | `ModelComparisonSimulator`, `ModelComparisonWorkflow`, `DeepSet(summary_dim=8, depth=1)`, `estimate()["model_probs"]` |
| Model_Comparison_Deep_Dive | PMP versus Bayes factor scoring rules, multi-rule pooling, GARCH-family comparison | `scoring_rules="exponential"`, `"logistic"`, lists of rules, `true_log_bfs_fn`, `TimeSeriesTransformer` |
| From_ABC_to_BayesFlow | Porting a pyABC Gillespie model | Simulator wraps ABC prior and model, `build_adapter`, `ConsistencyModel`, about 10 times fewer simulations than ABC for one dataset |
| SIR_Posterior_Estimation | Time-series counts, custom GRU summary, offline training, identifiability, real data and PPC | `as_time_series`, `log(p1=True)`, `@serializable` custom network, spline `CouplingFlow(depth=2)`, `standardize=None`, `samples_to_data_frame` |
| Lotka_Volterra_Point_Estimation | Rapid iteration with expert statistics and point estimation, then FlowMatching, then learned summaries | `ScoringRuleNetwork(MeanScore, QuantileScore)`, `recovery_from_estimates`, `calibration_ecdf_from_quantiles`, `TimeSeriesNetwork`, `drop` |
| Likelihood_Estimation | NLE for a g-and-k model, then PyMC NUTS | `inference_variables="x"`, `inference_conditions=[...]`, `standardize="all"`, `NeuralDistribution` |
| Ratio_Estimation | Contrastive NRE in PyMC, per-trial regression without retraining, diffusion decision model | `RatioApproximator(K=64)`, `MLP`, `CosineDecay(decay_steps=epochs*num_batches)`, `NeuralDistribution`, JAX only |
| Multimodal_Data | A set plus a time series with observation times | `FusionNetwork(backbones=..., head=...)`, `TimeSeriesTransformer(time_axis=-1)`, `group` last |
| Bivariate_Smoothing | Joint smoothing of whole latent trajectories | `AutoregressiveApproximator`, `RecurrentNetwork(return_sequences=True)`, `RecurrentDecoder`, explicit `OnlineDataset` and `OfflineDataset` |
| Diffusion_Models | Non-identifiable inverse kinematics, constraint guidance, masked conditionals | `DiffusionModel`, `guidance_kwargs`, `stop_time`, `subnet="diffusion_transformer"`, `fixed_target_prob`, masks |
| Compositional_Diffusion | Hierarchical diffusion decision model over 10,000 subjects | `CompositionalWorkflow`, `compositional_sample`, `compute_prior_score`, `ancestral_sample`, `sample_parallel` |
| Ensembles | Mixed generative and point members, data reuse, merged sampling | `EnsembleWorkflow`, `EnsembleApproximator`, `EnsembleDataset(data_reuse=0.5)`, `member_weights`, `merge_members=False` |
| Spatial_Data_and_Parameters | Parameters from images, and image generation conditioned on parameters | `ConvolutionalNetwork`, `DiffusionModel(subnet=bf.networks.ResidualUViT, prediction_type="velocity", noise_schedule="cosine")`, tiled conditions |
| Bayesian_Experimental_Design | Joint optimization of designs and posterior in a torch loop | `CouplingFlow().build(...)`, `log_prob` as loss, `torch.enable_grad()` |
| From_BayesFlow_1.1_to_2.0 | Migration map | See below |

## Migration from 1.x

| 1.x | 2.x |
|---|---|
| `bf.simulation.Prior`, `bf.simulation.Simulator`, `GenerativeModel` | `bf.make_simulator([prior, likelihood], meta_fn=...)`, functions return dicts |
| `configurator` function | `bf.Adapter` pipeline |
| `bf.amortizers.AmortizedPosterior`, `AmortizedLikelihood` | `bf.ContinuousApproximator` with roles set in the adapter |
| `InvertibleNetwork` | `bf.networks.CouplingFlow` or another `InferenceNetwork` |
| `bf.trainers.Trainer` | `approximator.compile(optimizer)` and `approximator.fit(...)`, or a workflow |
| `bf.diagnostics.plot_losses` and other `plot_*` | `bf.diagnostics.plots.*` and `bf.diagnostics.metrics.*` |

Roles are no longer inferred from the network type. Every key must be routed explicitly through the adapter or the workflow's naming arguments. Not every 1.x summary network was ported, and several defaults changed.
