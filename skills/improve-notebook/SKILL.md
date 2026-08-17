---
name: improve-notebook
description: Quality pass over Jupyter/marimo notebooks -- reproducibility, cell granularity, narrative, figure quality, and prose. Stacks an improve-code pass over the cell contents first, applies both, and reports the joint audit. Companion to improve-code and improve-tests; use when the user asks to clean up, tighten, professionalize, or review a notebook, or to make its figures presentable.
disable-model-invocation: false
metadata:
  tags: [notebooks, jupyter, marimo, matplotlib, code-quality, audit]
---

## Notebook-Quality Pass

Improve the notebooks named in the arguments and report what you changed. If none are named, work on the notebook currently being worked on. Ask for clarification only if there are no obvious candidates.

A notebook has one job the surrounding source files do not: it has to be *read*, top to bottom, by someone reconstructing an argument. Judge every cell against that. A notebook that produces the right numbers but reads as an undifferentiated wall of code has failed, and so has one that reads beautifully but cannot be re-run.

**This skill applies its findings; it does not stop at a report.** The only exceptions are the two classes of change that cost real time or real results -- see *What stays a proposal*.

## Input

$ARGUMENTS

The arguments are the notebook scope. There are no modifiers.

## Never edit a notebook file on disk

This is the hardest rule in this skill, and it precedes all of the work -- including the delegated `improve-code` pass, which must be told about it.

Do not use `NotebookEdit`, `Write`, `Edit`, or a script that rewrites the `.ipynb` JSON. A notebook is shared state across three places -- the file, the running kernel, and the open browser tab -- and the frontend autosaves its in-memory document on its own cadence. A disk write races that autosave, and whichever writes last wins. This has destroyed real work: edits that landed on disk and vanished on the next autosave, and inserted-and-executed cells wiped when the file was rewritten underneath an open tab.

Instead:

- Go through the notebook MCP bridge (`use_notebook`, `read_notebook`, `set_cell_source`/`overwrite_cell_source`, `insert_cell`, `delete_cell`, `run_cells`, `checkpoint_notebook`).
- **Read a cell's current source immediately before overwriting it.** The user edits cells between and during turns; a blind overwrite from a stale read clobbers their work.
- Re-fetch cell ids from `read_notebook` when a call reports an unknown id -- ids are reassigned on autosave and reload.
- Never `git checkout`, `git stash`, or otherwise rewrite a notebook file while its tab is open.
- If the bridge is unreachable, **say so explicitly and stop.** Ask the user to refresh the tab or reconnect, then wait. Do not silently fall back to disk. A disk edit is only safe for a notebook that is genuinely not open anywhere, and if there is any doubt, ask.
- The same applies to clearing outputs: ask the user to clear them in the UI rather than rewriting the file.

For marimo notebooks the file is `.py`, but the rule is unchanged -- route through the live editor, not a disk write.

## Stack improve-code first

The code inside the cells is still code, and this skill does not re-derive correctness, design, naming, or docstring findings. Run `improve-code` over the notebook before the notebook-level work, so the joint pass is a single coherent set of changes rather than two rounds of churn.

- **Skip it only if `improve-code --apply` has already run against this notebook in this session.** If it has, note that in the report and move on. If it ran without `--apply`, or ran against different files, it has not run for this purpose.
- Invoke it as `improve-code --apply <notebook paths>`, and **state the disk-edit prohibition in the invocation** -- `improve-code` will otherwise reach for `Edit`/`NotebookEdit` and clobber the live document. Every edit it makes goes through the bridge, reading each cell before overwriting it.
- Its Bugs tier stays opt-in, as that skill specifies. Carry its bug findings into the joint report unapplied.
- Keep its findings and yours separate in the report. They answer different questions and the user reads them differently.

If a finding could belong to either skill, the split is: `improve-code` owns what is true of the code regardless of where it lives; this skill owns what is true because it is in a notebook. A badly named variable is `improve-code`. That same variable being defined three cells after its first use is this skill.

## The source of truth

Your authority, in priority order:

1. **The user's global preferences** in `~/.claude/CLAUDE.md` -- already in your context. The code-style rules (one argument per line, keyword arguments, deliberate blank-line grouping, ASCII-only) apply inside notebook cells, and the prose rules apply to markdown cells. If this file and the checklist below ever disagree, the file wins -- re-read it.
2. **Project config and conventions**: `pyproject.toml` (line length, and whether notebooks are excluded from the formatter), any project `CLAUDE.md`, and any shared plotting or style module the repo already has.
3. **The surrounding notebooks.** Match the idioms of the series a notebook belongs to -- how it structures cells, where its helpers live, how its figures are styled. Local consistency beats personal preference, with one exception: do not pattern-match style off neighboring files the user has disowned. If the user has said a file is a negative example, it is not a license.

Cite which of these a change comes from, or state the concrete cost it removed. That keeps the report honest and lets the user overrule the judgment calls.

## Procedure

1. **Establish scope.** Named notebooks if given; otherwise the notebook edited this session. Say explicitly what you skipped if the scope is too large to cover exhaustively.
2. **Read the conventions before the notebook**, along with any shared plotting helper the project already has -- a figure change should reuse the house style, not invent one.
3. **Attach to the live notebook** through the bridge and `read_notebook` for the full cell list with ids, sources, and outputs. Note which cells have outputs, what their execution counts are, and whether that order is monotonic.
4. **Run the stacked `improve-code --apply` pass** unless it has already run this session (see above).
5. **Read the outputs, not just the source.** Whether a figure is legible, whether a cell dumps a raw DataFrame repr, whether a plot double-displays -- none of that is visible in the source. Use the bridge's image read for figures.
6. **Work the axes below**, applying as you go.
7. **Use `inspect_kernel` rather than adding a scratch cell** when you need to check the live namespace.

## The audit

### 1. Reproducibility and execution model

A notebook that only works in the kernel that happens to be running is a screenshot, not an analysis.

- **Does it run top to bottom in a fresh kernel?** Flag cells that depend on a name defined in a cell below them, or on a name that exists only because of a since-deleted cell. Non-monotonic execution counts are the tell -- check them.
- Flag hidden state: a cell that mutates a dataframe or dict in place and is safe to run once but wrong to run twice. Idempotent cells are the goal; where a cell genuinely cannot be, say so in its markdown.
- Flag unseeded randomness where a result is being reported, and paths that only exist on the author's machine.
- Add a progress indicator to expensive work that has none. Any multi-minute loop, per-item fit, or parallel fan-out gets a `tqdm.auto` bar -- without one there is no way to distinguish progress from a hang, and these jobs routinely outlast the bridge's execution timeout, which makes "no output yet" ambiguous.
- Flag long-running or fragile work that should be cached to disk rather than re-run on every kernel restart.
- **marimo only**: any name bound at a cell's top level enters the reactivity graph and must be globally unique -- including loop variables and context-manager bindings. Underscore-prefix common names (`msg`, `s`, `i`, `result`, `xs`) that are not exported to another cell, so they stay cell-private.

### 2. Cell granularity and narrative

One coherent step per cell. This is the finding the user reports most often, and the phrasing they used is "you tend to spew out blobs."

- **Split the monolithic cell.** A setup cell that imports, sets constants, opens a connection, runs a query, builds a panel, and transforms it is six cells. The natural seams are: imports and style, config constants, each query, each data pull, each transform, the assembly step, the run, and then one cell per figure.
- The test is whether a reader can run and inspect each step on its own. If a cell has to be edited to inspect an intermediate, it was doing too much.
- **Blank lines inside a cell are structural.** Separate distinct logical chunks with a single blank line -- compute, blank, plot; build, blank, check. Neither a dense unbroken block nor blank lines scattered with no logic to them.
- Split cells too long to hold in your head even when they are internally coherent -- past roughly a screen, a cell has stopped being a step.
- Fix ordering that fights the argument: setup buried after the first result, a helper defined three cells after its first use, a figure separated from the computation it displays.
- Flag heavy machinery that has outgrown the notebook. A function that is stable, reused, and worth testing belongs in the project's source tree, imported at the top -- not redefined inline. Moving it is a proposal, not an edit: it changes the repo, not the notebook.

### 3. Figures and output

Results are figures. This is where a notebook is either beautiful or embarrassing.

**Read `references/figures.md` in this skill's directory before writing or restyling any figure.** It carries the house conventions -- chrome, palettes, legend placement, subplot grids, the two-level date axis, and display mechanics -- as concrete code. Do not work from memory, and do not invent a style when the project already has a plotting module.

- **Replace raw output where a figure belongs**: printed `summary()` dicts, bare DataFrame and DataArray reprs, columns of numbers standing in for a result the reader is supposed to *see*. A table is fine when the reader needs exact values; it is not fine as the default presentation of a result.
- **A trailing `print` block is not how a professional notebook reports a result.** A cell that ends in three or four `print(f"...")` lines dumping labelled numbers is the single most common tell of a working notebook that was never finished. There is a strict order of preference, and the fix is almost always to move up it, not to reword the print:
  - *A figure*, when the result is a shape, a comparison, a trend, or an uncertainty. Most printed number blocks are figures that were never drawn.
  - *A DataFrame, displayed*, when the reader needs exact values. Build the frame and leave it as the cell's last expression so the frontend renders it as an HTML table. Never `print(df)` or `print(df.to_string())` -- that throws away the rendering and gives back fixed-width ASCII. One frame with named rows beats six `print` lines carrying the same numbers.
  - *A single `print`*, only for a genuinely scalar fact that has no table around it -- a count of divergences, a shape, which branch ran.
- **Never hand-align columns inside a format string.** Padding a label with literal spaces (`f"frontier growth    {x:.2f}"`) breaks the moment a label is edited, and it encodes a column width nothing enforces. Use f-string alignment so the width is declared: `f"{label:<28}{value:>8.2f}"`. If more than about three lines need to line up with each other, that is a table and belongs in a DataFrame.
- Cut interpretive commentary out of `print` calls entirely. A multi-line `print` explaining what the reader should conclude is a markdown cell at best and slop at worst; the density rules in the prose section apply to generated output too.
- Figures are production quality from the start, not "good enough for a notebook" -- these get screenshotted into notes and reports.
- Factor a figure repeated across cells into the shared helper module rather than leaving four copies of the same axis bookkeeping.
- Fix the double display, the missing save, and any save path pointing at a scratch or temp directory.
- Silence progress bars, verbose logging, and library chatter in cells whose output is meant to be read.
- Replace statistics computed by hand where the domain library already provides them -- arviz first for posterior and predictive quantities, then xarray reductions.
- **The same goes for plots, and it is missed more often.** Before drawing a distribution, a diagnostic, or a posterior by hand from `pdf`/`ppf`/quantile arrays, check whether the library that owns the object already draws it: preliz distributions have `plot_pdf`, arviz has the posterior and predictive plots, statsmodels and the state-space libraries have their own. A hand-rolled version is more code, drifts from the library's conventions, and usually omits the annotation the built-in gives free. Check the surrounding project for an established call pattern and match it.

### 4. Prose and polish

The markdown cells are the argument. They are also where LLM slop is most visible.

- **Density**: a terse header plus at most one orienting sentence per section. What we are doing, the code, the result. Cut interpretive paragraphs after a result, "what this bought us" commentary, and Takeaways or Summary cells. Interpretation the user asked for verbally goes in the chat, not the notebook. Where a notebook is genuinely a written report rather than a walkthrough, the standard is the austere academic register, which is a different length but the same discipline.
- **Cut bold-for-emphasis anywhere in markdown cells**, especially the tell of bolding the first few words of every bullet. Run-in headings are italic.
- **Cut non-ASCII characters** outside real LaTeX math: arrows, em and en dashes, section markers, middots, decorative bullets, check marks, emoji. Headings are plain ASCII -- `## 3. Turnover`, never a typographic section glyph. Numeric and date ranges use "to". Compounds use ASCII hyphens. Glyphs that are the actual content -- a check-mark config table, a Greek letter that is a column name, LaTeX math -- stay.
- Cut slop headers and callouts used as decoration, and LLM cadence: "It's worth noting", "Importantly,", "Note that", empty tricolons, hedging filler.
- **De-glyph generated matplotlib text too.** Titles and labels built in code are prose and follow the same rule.
- **A block of related equations is one `aligned` environment, not a stack of `$$` blocks.** Consecutive display equations set separately are spaced inconsistently and their relational operators do not line up, which is exactly where a reader checks a specification. Wrap them in `$$\begin{aligned} ... \end{aligned}$$`, align on `&=`, and separate rows with `\\`. Three things go wrong reliably and are worth checking by eye before moving on:
  - Use `aligned`, never `align`, inside `$$`. The unstarred `align` is itself a display environment, so nesting it inside `$$` is an error in MathJax and the block fails to render or renders as literal source. Standalone `\begin{align}` with no surrounding `$$` also works; mixing the two does not.
  - One `&` per row. A second alignment column silently changes the layout of every other row.
  - A missing `\\` merges two equations into one row. This is the most common breakage and the easiest to miss in source, because the text still reads correctly line by line.
  - Break a row too long for the page with `\\` and continue it with `&\quad`, rather than letting it overflow the container.
- Replace banner and divider comments used as section headings inside cells with blank lines.
- Fix stale markdown -- a cell describing what the code below it used to do.
- **Code style inside cells** follows the user's global rules: one argument per line when a call wraps, never a ragged grouping; keyword arguments throughout; imports at the top of the notebook, not scattered into the cell that first needs them. Check whether the project excludes notebooks from the formatter -- where it does, the user's visual-alignment layout is deliberate and must be preserved rather than reflowed to a hanging indent.
- Delete commented-out cells and dead scratch cells that survived the exploration.

## What to leave alone

- Correctness, performance, and design of the code inside the cells -- the stacked `improve-code` pass owns those. Don't re-derive them.
- Whether outputs should be committed, and repo-level notebook hygiene -- out of scope unless the project states a convention.
- Exploratory scratch cells the user has flagged as scratch. Not every notebook is a deliverable, and a working notebook is allowed to look like one.
- Consistent local idioms that merely differ from your taste.

## What stays a proposal

Everything else is applied. These are not, and asking first is not a formality here -- each one can cost the user hours or invalidate work in progress:

- **Reproducibility fixes that require reordering or re-running executed cells.** Re-running can cost hours, and reordering can invalidate results the user is mid-way through interpreting. Report the break precisely and let them decide.
- **A cell split whose re-run is expensive.** Splitting is a delete-and-insert and it destroys the original cell's outputs. Where the re-run is cheap, do it and confirm the new cells reproduce what the original showed. Where it is not, propose the boundaries instead.
- **Moving code out of the notebook into the project's source tree.** That is a repo change, not a notebook cleanup.
- **Bugs surfaced by the stacked `improve-code` pass**, per that skill's rules.

## Applying

- Every edit goes through the bridge, reading each cell before overwriting it. After a batch of inserts or edits, `checkpoint_notebook()` to persist.
- **Figure changes must be re-run and looked at.** Read the resulting image back through the bridge. A restyled figure you never rendered is a guess, and matplotlib will happily accept a call that silently does nothing.
- Prose and style edits are safe by construction. Run the checks over what you wrote before reporting -- `grep -nP '[^\x00-\x7F]'` and `grep -n '\*\*'` against the exported markdown -- rather than trusting that you avoided them.
- If a cleanup would change what the notebook computes, stop and reclassify it. This is a cleanup, not a re-analysis: the numbers and the argument stay as they are.

## Output

One joint report, written after the work, in the past tense. Group by notebook, and cite cells by both index and id (`cell 12 [a3f9]`), since indices shift as soon as anything is inserted.

Lead with a **Code** section carrying the stacked `improve-code` pass -- its own tiers, its own findings, its unapplied bugs -- or one line saying it had already run this session. Then the notebook tiers:

1. **Reproducibility** -- what did not run clean, and what was done about it. State the concrete failure: which cell breaks in a fresh kernel and why.
2. **Narrative** -- cell granularity, ordering, and structure. Name the splits by their new boundaries.
3. **Figures** -- what the reader sees now, and what was raw output before.
4. **Polish** -- prose, style violations, and cruft.

Format each entry as:

> `notebook.ipynb` cell N [id] -- *what was wrong in one line* -- why it cost the reader -- what you changed.

List everything held back under *What stays a proposal* separately, with the reason and the concrete change you would make. For a proposed split, give the cell boundaries explicitly rather than saying "split this up".

Don't pad. An entry that does not make the notebook meaningfully better is clutter, and this pass is partly about density.

Close with a two-line summary: counts per tier, what is still outstanding, and the dominant theme.
