# Figure conventions

The house style for figures produced in notebooks. Load this when a finding concerns
how a figure looks, or when writing or restyling one. These are defaults, not laws --
a project with its own plotting module outranks them, and the first thing to check is
whether one already exists.

## Where the styling lives

Repeated figures belong in a shared helper module next to the notebook
(`plotting.py`, or the project's existing equivalent), not copy-pasted into four cells.
A helper takes the data and an optional `ax`, and returns the `Figure`. Cells call the
helper; they do not carry 30 lines of axis bookkeeping.

A notebook series should look like one document. If two notebooks in the same directory
style the same quantity differently, that is a finding.

## Axes and chrome

- Drop the top and right spines.
- Titles are left-aligned and normal weight. No bold, no centered title.
- Label every axis, with units. When the units are obvious from the tick formatter
  (a percent axis), the label still names the quantity.
- A legend when there is more than one series; no legend when there is one. See
  *Legends* below for placement, which is not negotiable.
- Y-grid on, x-grid off, unless the x-axis is itself a measured quantity.
- Formatters match the quantity. A rate axis gets `PercentFormatter`, not raw decimals;
  a currency axis gets thousands separators. Raw floats on an axis that means something
  else is a defect.
- A small fixed palette, chosen once and reused, rather than whatever the default color
  cycle hands out. Keep the same series in the same color across every figure in a
  notebook.

## Legends

**Legends go outside the axes, never inside.** A legend box floating over the data hides
data, and where it lands depends on what the data happens to be doing that day.

The default is a single row, center-justified, below the plot -- or above it when the
figure's own title makes the top the natural place for it. One row means `ncol` equal to
the number of entries; drop to two rows only when a single row would squeeze the labels
illegibly narrow.

```python
handles, labels = ax.get_legend_handles_labels()

figure.legend(handles=handles,
              labels=labels,
              loc="lower center",
              bbox_to_anchor=(0.5, -0.05),
              ncol=len(labels),
              frameon=False)
```

Attach it to the figure, not the axes, so one legend serves a whole grid of subplots
rather than repeating per panel. With `constrained_layout` on, matplotlib reserves the
space; without it, leave room with `subplots_adjust` rather than letting the legend run
off the canvas. `frameon=False` -- the box adds nothing once the legend is outside the
data area.

Per-axes legends are the exception, justified only when panels show genuinely different
series. Repeating an identical legend on every panel of a grid is a finding.

## Grids of subplots

A grid whose plot count is not a multiple of the column count leaves a ragged last row.
Use `prepare_gridspec_figure` for these -- it centers the remainder.

```python
gs, plot_locs = prepare_gridspec_figure(n_cols=3, n_plots=8)
figure = plt.figure(figsize=(12, 8))

for (row_slice, col_slice), variable in zip(plot_locs, variables):
    ax = figure.add_subplot(gs[row_slice, col_slice])
    ...
```

It returns the `GridSpec` and a list of `(row_slice, col_slice)` pairs, one per plot, with
the trailing row's panels padded to sit centered under the full-width rows above.

It is a small free-floating utility with no canonical home, and it already exists in
several of the user's projects -- `gEconpy/plotting.py`, `rx_bonds/plotting.py`, and
`systematic_credit/backtest/linprog/plotting.py` all carry the same implementation. Import
it when the project in scope has a copy. When none does, re-rolling it is fine; put it in
the notebook's sidecar plotting module rather than in a cell, so the notebook stays a
narrative and the next notebook in the directory can import it too.

```python
def prepare_gridspec_figure(n_cols: int,
                            n_plots: int,
                            figure: plt.Figure | None = None) -> tuple[GridSpec, list]:
    remainder = n_plots % n_cols
    has_remainder = remainder > 0
    n_rows = n_plots // n_cols + int(has_remainder)

    gs = GridSpec(2 * n_rows, 2 * n_cols, figure=figure)
    plot_locs = [
        (slice(i * 2, (i + 1) * 2), slice(j * 2, (j + 1) * 2))
        for i, j in product(range(n_rows - int(has_remainder)), range(n_cols))
    ]

    if has_remainder:
        last_row = slice((n_rows - 1) * 2, n_rows * 2)
        left_pad = int(n_cols - remainder)
        for j in range(remainder):
            col_slice = slice(left_pad + j * 2, left_pad + (j + 1) * 2)
            plot_locs.append((last_row, col_slice))

    return gs, plot_locs
```

Copy it as it stands rather than reinventing the arithmetic -- the doubled grid is what
makes a half-column offset expressible. Don't hand-roll `plt.subplots` grid bookkeeping
where this applies.

## Date axes

`ConciseDateFormatter` mixes years and months on a single row and reads badly on
anything longer than a few months. Use a two-level axis: quarter-months near the axis in
a small font, and the year on a second row beneath in a larger font.

```python
import matplotlib.dates as mdates

ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=(1, 4, 7, 10)))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
ax.xaxis.set_minor_locator(mdates.MonthLocator())
ax.tick_params(axis="x", which="major", labelsize=7)

years = ax.secondary_xaxis(location="bottom")
years.xaxis.set_major_locator(mdates.YearLocator())
years.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
years.tick_params(axis="x", labelsize=9, pad=20, length=0)
years.spines["bottom"].set_visible(False)

ax.grid(visible=False, axis="x")
```

The year goes on the secondary axis, not the primary. Putting it on the primary drops
January wherever a year tick coincides with it.

## Labels and identifiers

Label a series by its human-readable name, never an opaque identifier. Where the data
carries only an id, resolve the description at the point the data is pulled and carry it
through to the plotting call -- do not resolve it inline in the plotting code, which
puts a lookup in the middle of a figure.

Generated titles and axis labels are prose and follow the prose rules: ASCII only, no
arrows or typographic dashes, no bold markup.

## Display mechanics

- A cell whose last expression is a `Figure` displays twice -- once as the returned repr,
  once from the inline backend. Suppress with a trailing `;` on the call. Do **not** use
  `plt.close`, which blanks the output of a `;`-suppressed cell entirely.
- Save when the figure is a deliverable. Save paths go where the user is already looking:
  the project root, the report directory, or a path they named. Never a scratch or temp
  directory -- a figure left there is lost.
- Silence library chatter in cells whose output is meant to be read: pass the quiet or
  `progress=False` flag rather than letting a progress bar or a sampler log land in the
  saved output.

## Statistics behind the figure

Compute the quantity with the library that owns it, then plot. For posterior and
predictive quantities that means arviz first (`az.hdi`, `az.summary`, `az.plot_ppc_dist`,
`az.loo`, `az.plot_loo_pit`), then xarray reductions over the `DataArray` where arviz has
no direct function. Draws raveled into numpy and quantiled by hand are a finding
regardless of how the result is displayed. Plot-axis arithmetic -- an `arange` for an
ECDF, a `linspace` for a colormap -- is not a statistic and is fine.

Show curves, not violins, when the quantity is a function of something. A violin per
knot throws away the shape the reader came for.
