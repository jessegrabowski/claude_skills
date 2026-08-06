---
name: improve-code
description: Full-spectrum code review -- correctness, performance, design (duplication, anti-patterns), and style against your stated conventions. Reports tiered findings and offers to apply them. Pass `style` to skip bug-hunting and report only behavior-preserving findings; pass `--apply` to apply them directly instead of asking first. Trigger even when the user doesn't name the skill -- "clean this module up", "make this more readable", "do a quality pass on parser.py".
disable-model-invocation: false
metadata:
  tags: [code-review, code-quality, refactoring, code-style, docstrings, audit]
---

## Code Review & Improvement Audit

Assess the code in the files named in the arguments -- correctness, design, and style -- and report concrete, justified improvements. If no files are specified, focus on the code currently being worked on (the uncommitted diff, or the files edited this session). Ask for clarification only if there are no obvious candidates.

Treat every line as if it will run in production at scale, maintained by someone sleep-deprived at 2AM. If it wouldn't survive that reality, it doesn't pass.

## Input

$ARGUMENTS

Two modifiers can appear anywhere in the arguments; everything else is the file scope.

- `style` -- **style-only mode**: skip the Bugs & correctness tier entirely and report only behavior-preserving findings (Structure, Violations, Polish).
- `--apply` -- **apply mode**: don't stop at the report. Apply every behavior-preserving finding (Structure, Violations, Polish) directly, then report what you changed. Bugs are still proposed for individual approval rather than applied -- see *Applying fixes*. `--apply style` therefore means "clean this up, touch nothing behavioral", which is the common case for a professionalism pass.

## The source of truth

Your authority, in priority order:

1. **The user's global coding preferences** in `~/.claude/CLAUDE.md` -- already in your context this session. These are not suggestions; they are the contract. The checklist below transcribes and operationalizes them. If this file and the checklist ever disagree (the file may have been edited since this skill was written), **the file wins** -- re-read it and follow it.
2. **Project config**: read the project's `pyproject.toml` (especially `[tool.ruff] line-length` / `[tool.black] line-length`) and any project `CLAUDE.md`. Line width, naming conventions, and idioms are project-specific, and the global rules explicitly defer to them. A 100-char habit reflowed into a 120-char project produces *inconsistent* code, which is itself a defect.
3. **The surrounding code.** Match the idioms, naming, and structure of the file and module you're in. Local consistency beats personal preference. Only override a consistent local idiom when it violates a stated rule from (1) or (2) -- and say so.

When you cite a finding, name which of these it comes from -- or, for bugs and design findings where the conventions are silent, state the concrete failure it causes. That keeps the audit honest and lets the user overrule you on the judgment calls.

## How to conduct yourself

- **Direct, specific, unapologetic.** No hedging with "maybe" or "consider", no empty praise. Cite the symbol and the line -- vague critique is useless critique. Assume the author is competent but rushed; dismantle the code, never the person.
- **Do not duplicate the formatter or linter.** Whitespace, quote style, import sorting, trailing commas, line-length *mechanics* -- ruff/black own these and fix them on save. Spending findings on them is noise. Your value is the layer they're blind to.
- **Don't pad the report.** A nit that doesn't make the code meaningfully better is clutter -- the same leanness you're auditing for applies to your own output. Every finding must earn its line.
- **Don't under-deliver either.** Padding is the loud failure; the quiet one is a timid audit that flags a rename and a reflow and calls it done while the cruft that actually makes the code hard to trust sits untouched. Read the code the way a demanding reviewer would -- go looking for what genuinely costs the next maintainer. An audit a maintainer wouldn't act on wasn't worth running.
- If the code is genuinely good, say so -- but only after trying to break it. Praise that survives a real attempt at destruction is worth something; praise that doesn't is noise.

## Procedure

1. **Establish scope.** Named files if given; otherwise the uncommitted diff (staged + unstaged), falling back to the files edited this session. When the scope is a diff, confine findings to the changed code and what it directly touches -- don't re-litigate untouched legacy code that happens to share a file. Audit a whole file only when it's named explicitly. If the scope is too large to audit exhaustively, prioritize (by centrality, churn, or the user's hint) and say explicitly what was skipped -- a truncated audit that presents itself as complete is worse than a scoped one.
2. **Read the config before the code.** `pyproject.toml`, project `CLAUDE.md`, lint and type-checker config.
3. **Run the mechanical tools, and split their output by role.**
   - *Formatter and linter* (`ruff check`, formatter dry-run): anything they flag is subtracted from your findings by construction -- it gets fixed on save, so reporting it is noise.
   - *Type checkers* (basedpyright / pyright / mypy -- whichever the project configures; check `pyproject.toml` and dev dependencies, and respect the project's choice): run on the target files and harvest the diagnostics as **leads for the Bugs tier**. Verify each against the code before reporting -- strict checkers produce false positives, and a parroted diagnostic is not a finding. Never resolve a diagnostic with a blanket `# type: ignore`; either the code is wrong or the annotation is.
     - `basedpyright` is installed as a global uv tool (`~/.local/bin/basedpyright`), so it's available even when the project doesn't vendor a checker -- invoke it with `basedpyright --pythonpath <project-venv-python> <files>` (e.g. `.pixi/envs/default/bin/python`) so it resolves imports against the project's environment. With no project pyright config it runs in **strict** mode and buries real signal under thousands of project-wide `reportUnknown*` / `reportMissingTypeArgument` / `reportUnusedCallResult` warnings; filter to the changed lines and lean on the high-value rules (`reportUnusedVariable`, `reportAttributeAccessIssue`, `reportCallIssue`, `reportArgumentType`, unreachable/possibly-unbound). Don't report a project's pre-existing strict-mode noise as a finding against the diff.
   - *IDE diagnostics*: if running inside an IDE integration where a diagnostics tool is available (e.g. `mcp__ide__getDiagnostics` under the JetBrains or VS Code extension), pull diagnostics for the target files and treat them the same way as type-checker output. Skip silently when unavailable.
4. **Note the baseline test status** before proposing anything -- is the suite green right now? Post-apply failures must be attributable.
5. **Read the code and audit** against the axes below.
6. **Verify Bugs-tier candidates.** When a cheap repro is feasible, write a scratch script and run it. Label every Bugs finding **confirmed** (reproduced) or **plausible** (by inspection only) -- never present inspection-level confidence as certainty.

## The audit

Each axis below states *why* it matters, because understanding the intent lets you judge the gray areas rather than pattern-match. Apply judgment, not a checklist-ticking reflex.

### 1. Correctness

Edge cases aren't "nice to have". Skipped in style-only mode.

- Hidden bugs, unhandled edge cases, undefined behavior, concurrency hazards, API misuse.
- If the code under review is numerical / scientific (array math, optimization, statistics, autodiff), read `numerics.md` in this skill's directory and apply its checklist as well. Skip it entirely for everything else -- don't import numerics concerns into a web handler.
- Error handling at real boundaries, not defensive theater. Flag silent exception swallowing -- bare `except:` or `except Exception: pass` that hides failures. Errors should be specific and loud.
- Input validation where it matters -- and only there.
- What happens when this breaks at 2AM? Failure modes should be observable (logging where the project logs), not silent.

### 2. Performance & leanness

Hot paths should be lean; obvious inefficiency is a defect even when it isn't premature optimization.

- Algorithmic complexity -- no silent O(n^2) where O(n) works.
- Redundant checks, work repeated inside a loop that could be hoisted out, recomputation of invariants, memory waste.

### 3. Design, duplication & abstraction

Abstractions must earn their keep -- and duplication and over-abstraction are the two failure modes of the same judgment call, so weigh them together.

- Is this the simplest thing that works? Is the complexity justified, or speculative? Flag generality that exists for a future that hasn't arrived.
- Flag real duplication: copy-paste-modify functions differing by one parameter, near-identical branches that could be table-driven or parameterized, the same logic block repeated across a module.
- But resist over-abstraction: don't extract a shared helper for a coincidental two-line overlap. The rule of three is a good prior. Two pieces of code that look alike today but change for different reasons are not duplication -- forcing them together couples them wrongly.
- **In test files, weigh the rule of three much more heavily against extraction.** A test's value depends on a reader auditing it as one self-contained block -- what was seeded, sampled, patched, and asserted, all visible without jumping to a fixture defined hundreds of lines away. Duplicated *setup* (repeated fixture-builder calls, monkeypatch/spy scaffolding, arrange-phase boilerplate) is usually worth keeping inline even at six or eight occurrences; a fragmented test costs the reader more than the duplication does. This is a strong presumption, not a prohibition -- flag an extraction when the block is long enough to bury the assertion it exists to set up, when it encodes an invariant that must stay identical across tests, or when a signature change would otherwise mean editing it everywhere. Deduplicate *source* files normally.
- Flag anti-patterns that hurt maintainability: boolean flags that make one function do two things (and the boolean trap `do_thing(True, False)` -- prefer keyword arguments or an enum); parameter lists too long to hold in your head; primitive obsession and dict-as-object where a dataclass or NamedTuple would self-document; mutable default arguments; hidden global state; functions that both compute and mutate; god functions/classes; leaky abstractions; a public surface larger than its actual clients need.
- Coupling and cohesion: things that change together should live together; a module reaching deep into another's internals (`a.b.c.d`) is a missing interface. Flag inheritance used for code reuse where composition would be simpler and flatter.
- Error-handling design should be consistent: one module shouldn't mix raising, returning None, and returning error codes for the same kind of failure. The API should follow least surprise -- sensible defaults, no argument whose meaning depends on another argument's value.
- Flag mixed abstraction levels within one function -- raw string-mangling next to high-level orchestration means a helper is missing.
- Flag functions doing several unrelated things, or grown long enough that they're hard to hold in your head -- suggest a split.

### 4. Naming & readability

The code should read as documentation; a good name removes the need for a comment.

- Names reveal intent. Flag cryptic abbreviations, single letters outside idiomatic/math contexts (`i`, `j`, `x`), and names that describe type rather than role (`data`, `tmp`, `obj`, `result2`).
- Flag magic numbers and strings that should be named constants.
- Names should be consistent with how the surrounding code names the same concept.

### 5. Narrative & shape

Intent should be visible in the shape of the code -- the structure itself is documentation.

- Prefer guard clauses and early returns over deep nesting; flag arrowhead-shaped code. The happy path should be prominent, error handling at the edges.
- Break up expression soup with named intermediates -- the name *is* the documentation.
- Analogous branches should be shaped analogously; asymmetry should signal a real difference, not accidental drift.
- Within a module, prefer top-down ordering: public API first, helpers below, reading order ~= call order.

### 6. Comments

Comments explain the *why*, never the *what* -- the code already says what it does.

- **Fewer is better.** Prefer no comment to one a better name would make redundant or that just restates the docstring; every comment can drift out of sync, so it has to change a reader's understanding to earn its place.
- Flag comments that narrate the code (`# increment counter`), restate the obvious, or have drifted out of sync with the code.
- Flag commented-out code -- delete it; that's what version control is for.
- Flag process/changelog comments embedded in source (`# previously we used a loop here`, `# fix for PR #123`, `# TODO (no owner, no context)`). Process belongs in commit messages, not the file.
- Comments should be reflowed to the project's full line width -- short broken-up lines waste vertical space.

### 7. Docstrings

A docstring is the source of truth for the *current* contract, read by someone who just cloned the repo and has never seen any prior version. This is the axis models most often get wrong, so weigh it heavily -- and the most common failure is bloat, not inaccuracy.

- **Brevity -- earn every sentence.** State the contract and stop. If the name and signature already say it, one line beats a paragraph, and a well-named test or private helper often needs no docstring at all. Rationale for *why the implementation works this way* is not the contract -- cut it (a one-line comment at most, usually the commit message). A docstring that reads like a mini-essay is a smell even when every sentence is accurate and active-voice.
- **Brevity decides *whether* a docstring exists; once it earns its place, it is structured** -- never freeform prose. Proper NumPy sections (`Parameters`, `Returns`, `Raises`, `Yields`, ...), one entry per item: a function returning a tuple gets a `Returns` section with one named entry per element, not a paragraph describing them. These two rules don't conflict -- the cut is between "no docstring" and "a short structured one", never "a chatty paragraph".
- **NumPy style, active voice**, with prose reflowed to the project's line width -- don't leave docstrings hard-wrapped at 70 chars in a 120-char project. "Compute the gradient", not "The gradient is computed"; "Raise ValueError if X", not "ValueError will be raised".
- **Contract, not commentary.** Flag anything that only makes sense as a note about recent work: explaining current behavior by contrasting with a previous version ("the earlier loop..."), references to audits/benchmarks/PRs/incidents, and "Notes"/"Discussion" sections or defensive "Note that..."/"Importantly..." prose that exists to justify a change rather than document the contract. Self-test each docstring: *would this still make sense to a fresh cloner who never saw an earlier implementation?* If not, cut the offending part.
- **Parameters**: `name : human readable type` -- `list of int`, not `list[int]`; describe genuinely nested types in prose rather than as a type-hint blob. Append `, optional` to optional args. Put the default value in the **last sentence** of the description, not on the type line.
- **Math** goes in `.. math::` directives (raw strings `r"""..."""` so backslashes survive), never as ASCII pseudo-code or backticked expressions. Inline, use `:math:` roles for mathematical symbols (`:math:`\alpha``) and double-backticks for code identifiers the reader could grep for (``` ``alpha`` ```).
- Use Sphinx roles for cross-references (`:func:`, `:class:`, `:mod:`).
- No module-level docstrings -- if a module's purpose isn't evident from its name and contents, the fix is a better name or a split, not a docstring.
- When you need exact section ordering or syntax (formatting `Parameters` for optional args, `*args`, or multiple returns), consult `references/numpydoc-style-guide.rst` in this skill's directory -- the canonical numpydoc spec -- rather than working from memory.

### 8. Modern idioms & types

Code should use the language as it is today and match the project's typing conventions. The bullets below are Python-specific; for other languages, apply the same principle with that language's modern idioms and the project's lint config as the authority.

- PEP 604 unions (`int | None`) and PEP 585 generics (`list[int]`) over `Optional`/`typing.List`. Flag `from __future__ import annotations` -- it's unwanted on supported Python versions.
- f-strings over `%`/`str.format`; context managers over manual open/close; `pathlib` over `os.path` string-mangling; `enumerate`/`zip` over index bookkeeping; comprehensions where they read more clearly than an accumulator loop (but not when they get so dense they obscure intent).
- Public functions/methods carry type hints -- the user treats them as documentation.
- Imports belong at the top of the module. Function-local imports are a habitual model tic and are almost never warranted -- flag them for hoisting. The rare exceptions (breaking a genuine circular dependency, guarding a heavy or optional dependency) are obvious from context; everything else moves up.
- Respect what the surrounding module already does; don't import a foreign idiom into code that's internally consistent.

### 9. Cruft & professionalism

The diff should look like it was written by someone who cleaned up after themselves.

- Flag leftover `print`/debug statements (use logging where the project does), dead/unreachable code, and unused imports or locals (these overlap with the linter -- only call them out if the linter clearly isn't catching them).
- Flag stray scratch/debug artifacts that shouldn't be committed; if a file genuinely shouldn't be tracked, the fix is a `.gitignore` entry, not deletion.
- Every dependency is a liability -- question a new one that the standard library or an existing dependency already covers.

## What to leave alone

- Anything ruff/black auto-fix. If running the formatter would resolve it, it's not your finding.
- Consistent local idioms that merely differ from your taste -- consistency is a feature.
- Test quality and coverage -- whether the assertions are the right ones, what isn't covered -- route those to `improve-tests`. Test files that are in scope are still audited as code (naming, cruft, structure, the duplication rules above).
- Speculative future-proofing (both suggesting it and demanding it).

## Output

Group findings by file. Within each file, sort into four tiers so the user can tell risk from obligation from opinion:

1. **Bugs & correctness** -- the behavior is wrong or fragile; fixing it *changes* behavior. State the concrete failure: what input or state triggers it, and what goes wrong. Mark each finding **confirmed** or **plausible** per the procedure. (Omitted in style-only mode.)
2. **Structure** -- behavior-preserving refactors: deduplication, splits, anti-pattern fixes, design cleanups. Correct by intent, but big enough that a reviewer would want a green test run behind them.
3. **Violations** -- breaks a convention the user has actually stated (global `CLAUDE.md`, project config). Name the rule it breaks.
4. **Polish** -- a zero-risk professional improvement where the stated conventions are silent. This is a judgment call and you should present it as one.

Format each finding as:

> `path:line` -- *one-line description of the issue* -- why it matters (the failure it causes, or the principle it violates) -- the concrete fix.

Show a tight before -> after only when it makes the fix unambiguous; don't quote large blocks. For the worst offenders, show the better approach as concrete code -- criticism without an alternative is half a finding. Be specific: cite the symbol and the line, never "improve naming throughout."

Close with a two-line summary (how many findings per tier, the dominant theme).

**In apply mode**, this report is written *after* the work, in the past tense, and covers what you changed rather than what you propose -- same tiers, same `path:line` specificity, so the user can audit the diff against it. Findings you deliberately held back still get listed, with the reason. Don't also emit a proposal-shaped report first; one report, after the fact.

## Applying fixes

By default, offer to apply, per tier -- all of it, one tier, or a subset the user picks. Under `--apply`, skip the offer and apply the behavior-preserving tiers straight away. Either way the per-tier rules below hold:

- **Bugs** are never bulk-applied, and `--apply` does not change that -- each one changes behavior, so it stays a separate proposal the user approves individually. When a bug fix is applied, promote its repro to a regression test in the project's test suite -- a confirmed bug without a test is a bug waiting to come back.
- **Structure** fixes are behavior-preserving by intent but not by construction -- after applying any, run the project's test suite and compare against the baseline status from the procedure; report the result. If a structure fix is large enough that you'd want the user to weigh in on the shape (splitting a public class, reorganizing a module's API), surface it as a proposal even under `--apply` rather than committing them to your design taste.
- **Violations and Polish** are safe by construction; apply and move on. If while applying you find that a "style" fix would actually alter behavior, stop and reclassify it instead.

Applying is a refactor, not a rewrite. The bar for every edit you make: a senior engineer reading the diff sees only changes that make the code clearer, tighter, or more idiomatic -- never a change in what it does. Public signatures, return types, side effects, and observable output stay as they are; when a cleanup would change the API contract, surface it instead of silently doing it.
