---
name: data-viz
description: Recipes for figures the user wants drawn a specific way, each with the layout rules and working matplotlib/arviz code. Use when drawing or restyling a figure that a recipe covers, such as posterior parameter plots, forest plots, or hierarchical effects against their parent distribution.
disable-model-invocation: false
metadata:
  tags: [matplotlib, arviz, figures, bayesian, notebooks]
---

# data-viz

Each recipe is a figure the user has specified exactly once and wants drawn the same way from then on. Find the recipe that covers the figure, follow its layout rules, and adapt its code to the data. When no recipe covers the figure, draw it to the general house style and leave this skill alone.

The general house style (chrome, legends, subplot grids, date axes, display mechanics) lives in `../improve-notebook/references/figures.md`. Read it as well. A recipe overrides it only where the two disagree.

## Using a recipe

- Put the recipe's helpers in the project's sidecar plotting module (`plotting.py` next to the notebook, or the project's existing equivalent). Import them from there, and do not paste them into a cell. If the module already has a copy, use that copy.
- Keep each helper's signature. A caller states every choice through keyword arguments, and the helper holds no defaults that encode a modeling decision.
- Always use arviz for anything posterior, and the figure must look like an arviz plot. Use the batteries-included plot that owns the figure type (`az.plot_forest`, `az.plot_dist`, `az.plot_ppc_dist`), handing it a custom `PlotCollection` when the layout needs faceting it does not offer. Assembling the figure from low-level visuals or raw matplotlib draws a matplotlib-looking plot even when the numbers are right. Compute with `.azstats` or xarray reductions over `chain` and `draw`, and never ravel draws into numpy.
- Render the figure and look at it before reporting it done.

## Recipes

| Recipe | Covers |
|---|---|
| `recipes/posterior-parameters.md` | Posterior plots of a fitted model's parameters: scalars together in one forest panel, and each hierarchical variable in its own panel over the one parent distribution its members share, all drawn with arviz |

## Adding a recipe

A new recipe is a file under `recipes/` plus one row in the table above. It states when it applies, the layout rules as the user gave them, how to build the inputs, and the helper code as it runs in a real project.
