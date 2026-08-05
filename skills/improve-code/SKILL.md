---
name: improve-code
description: Standards and professionalism pass over source code — refactors in place for self-documentation, naming, structure, docstrings, formatting, and idiom. Use whenever the user asks to improve, clean up, professionalize, tidy, polish, modernize, or raise the quality bar on code. Applies to test files too when they're part of the work; for a dedicated test-quality or coverage audit, prefer improve-tests. Trigger even when the user doesn't say "improve-code" explicitly — e.g. "clean this module up", "make this more readable", "do a quality pass on parser.py".
---

You will do a standards and professionalism pass over the files requested in the arguments, applying the improvements directly. If no files are specified, focus only on the code currently being worked on. Ask for clarification if there are no obvious candidates.

Test files are in scope: when they're among the requested files or part of the work in progress, hold them to the same standards as everything else — don't carve them out. The separate `improve-tests` skill is for a dedicated audit of test *quality and coverage*; reach for it only when that's specifically what the user wants, not as a reason to skip tests that are sitting right in front of you.

This is a refactor, not a rewrite. The bar is: a senior engineer reading the diff should see only changes that make the code clearer, tighter, or more idiomatic — never a change in what it does.

There are two ways to fail here, and the second is the one to watch for. The first is over-reaching — changing behavior in the name of cleanliness; the rest of this skill guards against that. The second, quieter failure is under-delivering: a timid pass that renames one variable, reflows a line, and calls it done while the cruft that actually makes the code hard to trust sits untouched. Read the code the way a demanding reviewer would — go looking for what genuinely costs the next maintainer, and fix it. A pass a maintainer wouldn't notice wasn't worth making.

## Input

$ARGUMENTS

## Before you start

- **Preserve behavior.** Public signatures, return types, side effects, and observable output stay the same unless the user asks otherwise. When a cleanup would change the API contract, surface it instead of silently doing it.
- **Match what's already there.** Infer the project's line length and style from its config (`pyproject.toml`, `setup.cfg`, `ruff.toml`, `.flake8`) and from the surrounding code. Adopt the codebase's conventions; don't impose your own.
- **Verify when it matters.** If the pass touched executable code and tests exist, run them — a professionalism pass that breaks something is a net loss. If the diff is confined to comments, docstrings, and formatting, skip the suite; there's nothing new to verify and the run is wasted effort.

## What "professional" means here

### Self-documentation first
- The code should explain itself through descriptive names and clear structure, so a comment becomes unnecessary. Reach for a better name or a smaller function before reaching for a comment.
- No abbreviations unless universally recognized (`id`, `df`, `url` are fine; `cfg_mgr`, `proc_res` are not).
- Functions are small and single-purpose. If a function needs a comment to mark where one responsibility ends and the next begins, it's two functions.

### Comments and docstrings, sparingly
- Comments are for future maintainers only: the *why* behind a non-obvious choice, a workaround, a subtle invariant. They are never section headings, changelog entries, or flags like `# changed this` / `# new`.
- A comment explaining *what* straightforward code does is a refactoring signal — improve the code so the comment isn't needed, then delete it.
- Write a docstring only when it adds information the signature and body don't already convey. No module docstrings. If you feel a docstring is needed just to say what the function does, that's a sign to refactor the function instead.
- The minimalism rule decides *whether* a docstring exists. Once you decide it earns its place, it is structured — never freeform prose. Use proper NumPy sections (`Parameters`, `Returns`, `Raises`, `Yields`, ...), one entry per item. A function returning a tuple gets a `Returns` section with one named entry per element, not a paragraph describing them. Collapsing structure into prose is the most common failure here; resist it.
- Use Sphinx roles for cross-references (`:func:`, `:class:`, `:mod:`) and the `:math:` role or a `.. math::` block for equations.
- When you need the exact section ordering or syntax (e.g. how to format `Parameters` for optional args, `*args`, or multiple returns), consult `references/numpydoc-style-guide.rst` — the canonical numpydoc spec — rather than working from memory.

  ```
  def rebuild_trained_shared(spec, idata):
      """Reconstruct trained shared variables from a fitted idata.

      Parameters
      ----------
      spec : GPModelSpec
          Model specification supplying the inducing-point and data variable names.
      idata : xr.DataTree
          Fitted inference data holding the trained point estimate.

      Returns
      -------
      shared_params : dict
          Maps each free RV's value variable to a shared holding its trained
          unconstrained value.
      replace_extras : dict
          Maps ``spec.Z_var`` / ``spec.X_var`` / ``spec.y_var`` to shareds holding the
          inducing points and training inputs/targets.
      """
  ```

### Structure and DRY
- Collapse genuine duplication into a shared helper — but only real duplication. Two pieces of code that happen to look alike today yet change for different reasons are not duplication; forcing them together couples them wrongly.
- Apply the rule of three: the second occurrence is tolerable, the third is the signal to factor out. Don't abstract on the first sight of a pattern — premature abstraction is as costly as duplication, and you rarely know the right shape until the third case shows you.
- **In test files, weigh the rule of three much more heavily against extraction.** A test's value depends on a reader auditing it as one self-contained block — what was seeded, sampled, patched, and asserted, all visible without jumping to a fixture defined hundreds of lines away. Duplicated *setup* (repeated fixture-builder calls, monkeypatch/spy scaffolding, arrange-phase boilerplate) is usually worth keeping inline even at six or eight occurrences; a fragmented test costs the reader more than the duplication does. This is a strong presumption, not a prohibition — extract when the block is long enough to bury the assertion it exists to set up, when it encodes an invariant that must stay identical across tests, or when a signature change would otherwise mean editing it everywhere. When you do extract, keep the call site expressive enough that the test still reads on its own. Deduplicate *source* files normally.
- Before writing a new helper, check whether one already exists — in the same module, in the project's utils, or in a dependency. Reinventing an existing utility is its own form of duplication.
- Prefer simplicity over cleverness. An abstraction that exists mainly to look clever, or a dense one-liner that's proud of itself, costs the next reader more than it saved the author — unwind it. When complexity has crept in, refactor it out rather than commenting around it.
- Dead code, unreachable branches, unused imports/variables, and commented-out scaffolding go. Stale markers go too: a TODO naming a real, current follow-up can stay, but "clean this up later" with no owner and no meaning is an apology, not information — cut it.
- Imports belong at the top of the module, not buried inside functions. Local imports are a habitual model tic and are almost never warranted — hoist them up. The rare exceptions (breaking a genuine circular dependency, or guarding a heavy/optional dependency) should be obvious from context; everything else moves to the top.

### Formatting
- Reflow to use the full project line width — don't leave text wrapped short out of habit when the project allows wider lines, and don't overflow it either.
- Follow PEP 8. Where an autoformatter (black, ruff) governs the project, defer to it rather than hand-formatting against it.

### Performance with judgment
- Prefer vectorized operations over explicit loops where it's natural (NumPy, pandas, Polars).
- Hot paths earn their efficiency; cold paths earn their readability. Don't obfuscate a once-per-run setup function for a speedup that never matters, and don't leave an inner loop naive when it runs millions of times. Optimize where it counts, stay clear everywhere else.

## What to leave alone
- Intentional style the project has clearly committed to, even if it's not your preference.
- Behavior, including edge-case quirks, unless the user flagged them as bugs. This skill polishes; it doesn't fix logic.
- Input-validation and other obviously-correct boilerplate — tightening it rarely pays for the churn.

## Reporting
After applying the pass, give a short summary grouped by kind of change (naming, structure, docstrings, formatting, performance), noting anything you deliberately left untouched and any cleanup you held back because it would touch behavior or the public API.

Be specific: name the symbol and cite `file:line`. "Renamed `proc_res` → `pricing_result` at pricer.py:88" tells the reader something; "improved naming and structure" does not. A summary that could describe a cleanup of any file means you're reporting the category, not the work you actually did.
