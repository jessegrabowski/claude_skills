---
name: when-in-rome
description: Idiom-conformance audit -- reads at least two peer files in the current project, derives the codebase's own conventions (naming, module layout, typing, error handling, local helpers, test idioms), and evaluates the scoped files against them. Reports Reinvention / Deviation / Tension findings and offers to apply them. Pass `--like <paths>` to name the exemplar files yourself, and `--apply` to apply directly instead of asking first. Use whenever the question is whether code fits the repo it lives in -- "does this match how the rest of the codebase does it", "make this look like it belongs here", "is this idiomatic for this project", contributing to an unfamiliar or upstream repo, or a PR that a maintainer might bounce for not following house style.
metadata:
  tags: [code-style, idioms, consistency, code-quality, audit]
---

## Idiom-Conformance Audit

Evaluate the files named in the arguments against the conventions of the codebase they live in, and report where they diverge. If no files are specified, use the code currently being worked on (the uncommitted diff, or the files edited this session). Ask for clarification only if there are no obvious candidates.

"Idiomatic" here has no fixed meaning. It is whatever the maintainers of this repository consistently do, and the only way to learn it is to read their code. A function that is correct and clean by general standards still costs review time if it is shaped unlike every function around it: the reader has to stop and work out whether the difference means something. The goal is code a maintainer reads as their own.

## Input

$ARGUMENTS

Two modifiers can appear anywhere in the arguments. Everything else is the file scope.

- `--like <path> [<path> ...]` -- use these files as the exemplars and skip automatic selection. Every path after `--like` up to the next modifier is an exemplar. Fewer than two is allowed only if the user names exactly one, and the report says the profile rests on a single file.
- `--apply` -- apply the Reinvention and Deviation findings directly, then report what changed. Tension findings stay proposals. See *Applying fixes*.

## The source of truth

The exemplars are the authority. This is the deliberate difference from `improve-code`, which puts the user's global preferences first and treats the surrounding code as a tiebreaker. Here the surrounding code is the standard being measured against.

1. **Codified project conventions** -- `pyproject.toml` (ruff, black, isort, pytest, type-checker sections), `setup.cfg`, `.editorconfig`, a project `CLAUDE.md`, `CONTRIBUTING.md`, and a style section in the developer docs if one exists. These are idioms the maintainers wrote down, so they outrank anything inferred.
2. **The idiom profile** built from the exemplars (see *Procedure*). These are idioms the maintainers practice but never wrote down.
3. **The user's global preferences** in `~/.claude/CLAUDE.md` do not override (1) or (2). Where a codebase idiom contradicts a stated global rule, the finding goes in the Tension tier with both sides shown, and the user decides each one. Where the codebase has no idiom on a point, the global rules are out of scope for this skill -- that is `improve-code`'s job.

Every finding cites its evidence: the config key, or the exemplar `path:line` locations that establish the idiom.

## Procedure

### 1. Establish scope and classify it

Named files if given. Otherwise the uncommitted diff (staged and unstaged), falling back to the files edited this session. When the scope is a diff, confine findings to the changed lines and what they directly touch.

Classify each scoped file by role: library module, CLI or entry point, test file, conftest/fixture module, notebook, script, config. Roles have different idioms -- a test file is compared against test files, a CLI against CLIs -- so each role in scope gets its own exemplar set.

### 2. Choose exemplars

Skip this step under `--like`.

Pick at least two exemplars per role, and up to four when the role is large enough to have them. Rank candidates by:

- **Same role and layer.** A peer module in the same package beats a module of the same role elsewhere. For a test file, the tests of sibling modules come first.
- **Proximity.** Siblings, then the parent package, then the rest of the repo.
- **Maintenance.** Code that the core maintainers wrote or touched recently reflects current practice. `git log --format='%an %as' -- <file> | head` shows who and when. Prefer files with several authors over a file one contributor wrote once, since a single-author file shows one person's habits.
- **Comparable size and complexity.** A 30-line utility module says little about how a 600-line estimator class should be organized.

Exclude generated code, vendored code, migrations, `_version.py`-style boilerplate, and files that comments or docs mark as legacy or deprecated.

Scoped files and exemplar status: when the scope is a diff, the unchanged portion of a scoped file is valid evidence, often the best available, because it is the file's own established idiom. When a whole file is in scope, it cannot be its own exemplar, since judging a file against itself finds nothing. In both cases at least two exemplars must come from outside the scope.

If fewer than two qualifying peers exist (a new project, a one-of-a-kind module), widen the radius and say so. If the repo still has fewer than two, report the shortfall, build the profile from what exists, and mark every finding low-confidence.

State which exemplars were chosen and the one-line reason for each before the findings. The user should be able to reject a bad choice and re-run with `--like`.

### 3. Build the idiom profile

Read each exemplar in full. Skimming misses exactly the habitual details this audit exists to find. Record each convention observed, with its evidence and its strength:

- **Consistent** -- every exemplar that has occasion to show it does so the same way.
- **Majority** -- most do, with an exception that has no visible reason.
- **Split** -- no dominant pattern. The codebase has no idiom here, and nothing is enforced.

Corroborate before relying on an idiom. Four files can share a quirk the rest of the repo does not, so check the important ones repo-wide with a quick search: `rg -c 'logging.getLogger\(__name__\)'` against `rg -c '^\s*print\('`, `rg -l 'from __future__ import annotations' | wc -l` against the module count, and so on. Promote or demote the strength according to what the search shows.

Watch for idioms in motion. If the newest code does X and older code does Y, the codebase is migrating toward X, and X is the idiom even though Y may have more instances. `git log` dates on the exemplars, or a recent commit that converts Y to X, are the evidence.

### 4. Subtract the mechanical layer

Anything the configured formatter or linter enforces -- whitespace, quote style, import sorting, line length -- is fixed on save. Do not report it. If the project has ruff or black configured, run it in check mode on the scope and treat its output as already handled.

### 5. Evaluate the scope against the profile

Compare each scoped file against the profile for its role. Only consistent and majority idioms are yardsticks.

## What to look for

These are the dimensions where codebases differ most. They are phrased for Python, and the analogous questions apply in any language. Not every dimension will have an idiom in every repo, and the profile should record only what the exemplars actually show.

### Local vocabulary and helpers

This is the highest-value dimension. The most expensive non-idiomatic code reimplements something the project already has: a hand-rolled input check where the package has a `validate_*` helper, a manual RNG setup where there is a `get_rng(seed)` utility, a fresh `assert np.allclose` where the test suite uses a shared `assert_close` wrapper. Before concluding that a block of scoped code is novel, search for the project's own helper. Grep for the key operation, look in `utils`, `_utils`, `helpers`, `compat`, `testing`, and `conftest.py` modules.

Vocabulary counts too. If the codebase calls the concept `n_obs`, the scoped file should not call it `num_observations`. Prefixes and verbs follow the same rule: `get_` versus bare nouns for accessors, `make_` versus `build_` versus `create_` for factories, `is_`/`has_` for predicates.

### Module shape

- Import style: absolute or relative within the package, `import module` or `from module import name`, the standard aliases (`np`, `pd`, `pt`, `xr`), and whether optional dependencies are guarded.
- Ordering: public API first or helpers first, where constants live, whether `__all__` is declared.
- Granularity: how long functions typically are, and whether logic tends to live in free functions or classes.

### Signatures and API shape

- Keyword-only markers (`*`), argument ordering conventions (data first, config last), default-value style (`None` sentinel then resolve, or literal default).
- Return conventions: tuples, named tuples, dataclasses, dicts, or mutated arguments.
- Annotation density and syntax: fully annotated or only public functions, `X | None` or `Optional[X]`, `from __future__ import annotations`, and where `TYPE_CHECKING` imports go.

### Data and errors

- The container of choice for structured values: dataclass, `NamedTuple`, `TypedDict`, pydantic model, attrs, plain dict.
- Error style: a project exception hierarchy or built-ins, raising versus returning `None`, the shape of error messages (f-string with the offending value, a sentence, a fixed phrase), and `warnings.warn` categories.
- Logging: module logger, a project logger factory, or none.

### Documentation

- Docstring format (numpydoc, Google, reST, none) and which functions get one -- every public function, only non-obvious ones, or none.
- Which sections appear (`Examples`, `Notes`, `References`), how types are written in `Parameters`, and whether private functions carry docstrings.
- Comment density and placement.

### Test idioms

Applies when a test file is in scope, with test files as its exemplars.

- Layout: one test file per source module, class-grouped or flat functions, test naming pattern (`test_<unit>_<condition>`, `test_<behavior>`).
- Fixtures: which shared fixtures `conftest.py` already provides, fixture scope habits, and whether the suite builds inputs through fixtures or inline.
- Parametrization: `pytest.mark.parametrize` with `ids=`, `pytest.param` with marks, or stacked decorators.
- Assertions: the project's numerical-comparison helper and its tolerances, `pytest.raises(match=...)` usage, and any custom assertion helpers.
- Randomness and markers: how RNGs are seeded, which custom marks exist (`slow`, `gpu`), and how expensive tests are gated.

## What to leave alone

- Anything the formatter or linter fixes.
- Split idioms. When the exemplars disagree, there is no house style to violate.
- Correctness, performance, and general design quality. Route those to `improve-code`. A finding here says "this differs from how the codebase does it," never "this is wrong."
- Test usefulness and coverage. Route those to `improve-tests`.
- Old idioms the codebase is moving away from. Do not ask new code to imitate the legacy side of a migration.

## Output

Open with the evidence, so the user can check the yardstick before reading the measurements:

1. **Exemplars** -- per role, the chosen files and one line each on why.
2. **Idiom profile** -- a compact table of the idioms that drove findings: the idiom, its strength, and two or more `path:line` citations. Leave out idioms that the scope already follows, unless the user asked for the full profile.

Then group findings by file, in three tiers:

1. **Reinvention** -- the scoped code reimplements a helper, fixture, or constant the project already provides. Name the existing one and its location.
2. **Deviation** -- the scoped code departs from a consistent or majority idiom. Name the idiom and its strength.
3. **Tension** -- the codebase idiom contradicts a rule in `~/.claude/CLAUDE.md`. Show both sides: the idiom with its evidence, the global rule quoted, and what the code would look like under each. Make no recommendation. These are the user's call, one by one.

Format each finding as:

> `path:line` -- *how the code departs from the idiom* -- the evidence (`exemplar:line`, `exemplar:line`, or the config key) -- the concrete change.

Show a short before -> after when the change is not obvious from the description. Never write "follow project conventions throughout" -- cite the line.

Close with a two-line summary: counts per tier, and the dominant theme.

If the scope already conforms, say so, and say which idioms it was checked against. A clean result with a visible profile is useful. A bare "looks consistent" is not.

**In apply mode**, write this report after the work, in the past tense, covering what changed. Same tiers, same `path:line` specificity. Tension findings appear as open questions, and anything deliberately held back is listed with the reason.

## Applying fixes

By default, offer to apply, per tier. Under `--apply`, apply Reinvention and Deviation directly.

- **Reinvention** fixes swap local code for a project helper, and the helper's edge-case behavior may differ from the code it replaces (different defaults, different exceptions, different handling of empty input). Read the helper before substituting it. If the behaviors differ in a way a caller could observe, surface the finding as a proposal instead of applying it.
- **Deviation** fixes are behavior-preserving by intent. Renames must update every reference, including tests and docs. A rename of a public symbol changes the API, so surface it as a proposal even under `--apply`.
- **Tension** findings are never applied without the user's per-finding decision, and `--apply` does not change that.

After applying anything, run the test suite for the touched modules and report the result against a baseline taken before the first edit.
