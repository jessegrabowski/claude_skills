# Posterior parameters

Use this recipe to show a fitted model's parameter posteriors. It replaces a grid of per-variable density plots (`az.plot_dist`, `az.plot_posterior`) and a single forest plot of every variable.

Every panel is an `az.plot_forest` under the `arviz-variat` style: hollow mean markers, a thick 50% HDI trunk, a thin outer HDI twig, and a labels column. Everything around the forest goes through the `PlotCollection` interface, so the figure is arviz's own drawing end to end:

- The parent band is `azp.add_bands` and the parent mean is `azp.add_lines`.
- The legend is `PlotCollection.add_legend` over the dims those two helpers map their aesthetics to.
- Titles and the bare labels-column axes are `arviz_plots.visuals` functions (`labelled_title`, `remove_axis`) applied with `PlotCollection.map`.
- The style is the `arviz-variat` template, scoped with `plt.style.context` so the rest of the notebook keeps its own style. `azp.style.use` sets the same template globally.

Do not pull axes out of `plot_collection.viz` to call matplotlib on them (`axvspan`, `get_legend_handles_labels`, `set_yticks`, spines), and do not assemble the members from low-level visuals (`line_x`, `scatter_x`) or raw matplotlib. Either one produces a figure that looks like matplotlib and bypasses the aesthetics that `add_legend` reads.

## Layout

There are two figures, split by variable shape.

- Scalar variables that stand alone go together in one forest panel, one row per variable, with chains combined.
- Each hierarchical variable gets its own panel, one row per member. The panels sit side by side and share the y-axis, so a member lines up across panels.
- Every hierarchical panel draws its parent distribution behind the members: the parent's mean as a light dashed vertical line, and the parent's 95% HDI as a light shaded band across the full panel height. The panel exists to show how the members compare with the inferred distribution they are drawn from.
- The variable name is the panel title. The labels column carries only the member labels (the dim coordinate), never the variable name.
- Members are forest rows: the mean as a hollow point, the 50% HDI as a thick trunk and the 95% HDI as a thin twig. Each variable's panel keeps its own labels column, so every panel reads on its own while the rows stay aligned.

## The parent is one distribution

Every member of a hierarchy is drawn from the same parent, so each panel has exactly one parent mean and one parent band. Never draw a band or mean line that differs by member.

A model can scale its members' prior by a known per-member constant, such as `oas_rating ~ Normal(oas_level * ladder[rating], oas_tau_rel * ladder[rating])`. Here the members are not exchangeable in their own units. Plot them in the units where they share a parent, `oas_rating / ladder ~ Normal(oas_level, oas_tau_rel)`, and name the panel for that quantity (`oas_rating_in_ladder_units`). A non-centered variable shows its member values (`log_sigma_rating`), never the raw offsets (`log_sigma_rating_z`).

## Building the inputs

The helper takes three `xr.Dataset`s with the same variable names, one variable per panel:

- `members` holds the member draws over `chain`, `draw` and the member dim.
- `parent_means` holds each parent mean's posterior draws over `chain` and `draw`.
- `parent_draws` holds one new member drawn from the parent per posterior draw. Its HDI is the band. It integrates over the parent's uncertainty in both mean and scale, which the posterior of the parent mean alone would understate.

For Normal parents, build `parent_draws` from the means, the scales and one seeded standard-normal `DataArray` over `chain` and `draw`:

```python
posterior = idata["posterior"].dataset
oas_ladder = xr.DataArray(OAS_LADDER, coords={"rating": RATING_BUCKETS})

members = xr.Dataset({"oas_rating_in_ladder_units": posterior["oas_rating"] / oas_ladder,
                      "log_sigma_rating": posterior["log_sigma_rating"]})
parent_means = xr.Dataset({"oas_rating_in_ladder_units": posterior["oas_level"],
                           "log_sigma_rating": posterior["log_sigma_mu"]})
parent_sds = xr.Dataset({"oas_rating_in_ladder_units": posterior["oas_tau_rel"],
                         "log_sigma_rating": posterior["log_sigma_tau"]})

parent_rng = np.random.default_rng(sum(map(ord, "parent distribution draws")))
parent_noise = xr.DataArray(parent_rng.standard_normal(posterior["oas_level"].shape),
                            dims=posterior["oas_level"].dims)
```

When a member-scaling constant (a ladder, a design matrix) is defined inside the model builder, lift it to a module-level constant that both the model and the plot cell read. Do not copy the literal into the plot cell.

## Calls

```python
plot_scalar_forest(idata,
                   var_names=[rv.name for rv in model.free_RVs if rv.ndim == 0],
                   hdi_prob=0.95);

plot_hierarchical_effects(members,
                          parent_means=parent_means,
                          parent_draws=parent_means + parent_sds * parent_noise,
                          dim="rating",
                          hdi_prob=0.95);
```

## Helpers

These run against arviz 1.x (arviz-plots, arviz-stats, arviz-base). Several mechanics in them are not obvious from the arviz docs:

- `az.plot_forest` alone cannot facet variables side by side. Given its own grid, it lays out one labels column and one forest column and stacks variables as row blocks. The helper builds a `PlotCollection.grid` over `__variable__` and the `column` dim that `plot_forest` expects (`labels`, `forest`), maps `y` and `overlay` over `__variable__` and the member dim with one position list so the rows line up across variables, and passes the collection to `plot_forest`. `visuals={"ticklabels": False}` is required, because `plot_forest` otherwise sets x tick labels on a single labels column and fails on several.
- `add_bands` and `add_lines` take no `coords` argument. Passing them a Dataset that carries a size-1 `column=["forest"]` dim confines them to the forest columns, because a Dataset reference is used as is.
- Give the band and the line separate reference dims (`parent_band`, `parent_line`). Each helper maps its overlay aesthetic to its own dim, and a shared dim with different coordinates gives `add_legend` conflicting mappings.
- `add_lines` maps `overlay_ref` per variable, which `add_legend("parent_line")` cannot match. Registering the mapping first with `generate_aes_dt` and `update_aes_from_dataset` makes it shared across variables, and `add_lines` then reuses it.
- `add_legend` draws line miniatures from `visual_kwargs` without resolving arviz aliases (`"B2"`, `"C1"`), so resolve them with the backend's `dealiase_line_kwargs`. Pass `title=""`, because `title=None` falls back to the dim name.

```python
from collections.abc import Sequence

import arviz as az
import arviz_plots as azp
import matplotlib.pyplot as plt
import xarray as xr
from arviz_base.labels import BaseLabeller
from arviz_plots.backend.matplotlib.legend import dealiase_line_kwargs
from arviz_plots.visuals import labelled_title, remove_axis
from matplotlib.figure import Figure


def plot_scalar_forest(idata, *, var_names: Sequence[str], hdi_prob: float) -> Figure:
    """Return one forest panel holding every scalar in ``var_names``, chains combined."""
    with plt.style.context("arviz-variat"):
        plot_collection = az.plot_forest(idata,
                                         var_names=list(var_names),
                                         combined=True,
                                         ci_kind="hdi",
                                         ci_probs=(0.5, hdi_prob),
                                         backend="matplotlib")
    return plot_collection.viz["figure"].item()


def plot_hierarchical_effects(members: xr.Dataset,
                              *,
                              parent_means: xr.Dataset,
                              parent_draws: xr.Dataset,
                              dim: str,
                              hdi_prob: float) -> Figure:
    """Return one forest panel per variable in ``members``, over that variable's parent.

    Parameters
    ----------
    members : xr.Dataset
        Posterior draws of each hierarchical variable's members, over ``chain``, ``draw`` and
        ``dim``.
    parent_means : xr.Dataset
        Posterior draws of each variable's parent mean, over ``chain`` and ``draw``, keyed like
        ``members``.
    parent_draws : xr.Dataset
        One draw of a new member from each variable's parent per posterior draw, keyed like
        ``members``.
    dim : str
        The member dim, one forest row per label.
    hdi_prob : float
        Probability mass of the outer member HDI and of the parent HDI.

    Returns
    -------
    figure : Figure
        The figure holding a labels column and a forest column per variable.
    """
    band_label = f"parent {hdi_prob:.0%} HDI"
    parent_band = (parent_draws.azstats.hdi(prob=hdi_prob)
                   .rename(ci_bound="band_dim")
                   .expand_dims(parent_band=[band_label], column=["forest"]))
    parent_line = (parent_means.mean(dim=("chain", "draw"))
                   .expand_dims(parent_line=["parent mean"], column=["forest"]))

    n_members = members.sizes[dim]
    figure_kwargs = {"sharey": True,
                     "width_ratios": [0.6, 3] * len(members),
                     "figsize": (5 * len(members), 0.45 * n_members + 1.5)}
    band_miniature = dealiase_line_kwargs(color="B2", alpha=0.15, width=8)
    line_miniature = dealiase_line_kwargs(color="B2", linestyle="C1")

    with plt.style.context("arviz-variat"):
        plot_collection = azp.PlotCollection.grid(members.expand_dims(column=["labels", "forest"]),
                                                  cols=["__variable__", "column"],
                                                  backend="matplotlib",
                                                  aes={"y": ["__variable__", dim],
                                                       "overlay": ["__variable__", dim]},
                                                  y=list(range(n_members))[::-1],
                                                  figure_kwargs=figure_kwargs)

        # add_lines would map overlay_ref per variable, which add_legend cannot match to the
        # parent_line dim alone, so the mapping is registered shared across variables first.
        line_aes = plot_collection.generate_aes_dt({"overlay_ref": ["parent_line"]}, parent_line)
        for aes_key, child in line_aes.children.items():
            plot_collection.update_aes_from_dataset(aes_key, child.dataset)

        azp.add_bands(plot_collection,
                      parent_band,
                      ref_dim=["parent_band", "band_dim"],
                      visuals={"ref_band": {"alpha": 0.15}})
        azp.add_lines(plot_collection,
                      parent_line,
                      ref_dim="parent_line")
        az.plot_forest(members,
                       plot_collection=plot_collection,
                       combined=True,
                       ci_kind="hdi",
                       ci_probs=(0.5, hdi_prob),
                       labels=[dim],
                       visuals={"ticklabels": False})
        plot_collection.map(remove_axis,
                            "labels_axis",
                            coords={"column": "labels"},
                            ignore_aes=plot_collection.aes_set,
                            axis="both")
        plot_collection.map(labelled_title,
                            "title",
                            coords={"column": "forest"},
                            ignore_aes=plot_collection.aes_set,
                            subset_info=True,
                            labeller=BaseLabeller())

        # Legend miniatures take visual_kwargs verbatim, so the arviz aliases the band and line
        # were drawn with are resolved through the backend's own dealiaser.
        plot_collection.add_legend("parent_band",
                                   visual_kwargs=band_miniature,
                                   title="",
                                   loc="outside lower left",
                                   frameon=False)
        plot_collection.add_legend("parent_line",
                                   visual_kwargs=line_miniature,
                                   title="",
                                   loc="outside lower right",
                                   frameon=False)

    return plot_collection.viz["figure"].item()
```
