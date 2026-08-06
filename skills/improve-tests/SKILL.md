---
name: improve-tests
description: Quality and coverage audit of test files — usefulness, readability, coverage judgment, and maintainability. Reports findings as Remove / Improve / Add and offers to apply them. Pass `--apply` to apply them directly instead of asking first. Use when the user asks to improve tests, review test quality, audit test coverage, or professionalize tests.
tags: [testing, pytest, code-quality, audit]
---

## Test-Quality Audit

Assess the tests in the files named in the arguments and report concrete, justified improvements. If no files are specified, focus on the tests currently being worked on. Ask for clarification only if there are no obvious candidates.

A test suite earns its keep by catching real bugs and by telling the next reader what the code is supposed to do. Judge every test against those two jobs. A test that does neither is a liability — it costs CI time, it costs attention at review, and it has to be updated every time the code moves.

## Input

$ARGUMENTS

`--apply` may appear anywhere in the arguments; everything else is the file scope. Under `--apply`, don't stop at the report: make the **Improve** and **Add** changes directly, then report what you did. **Remove** stays a proposal — deleting a test destroys coverage, and that's the user's call. See *Applying fixes*.

## The source of truth

Your authority, in priority order:

1. **Project testing conventions** — read `tests/CLAUDE.md` if it exists, plus any project-root `CLAUDE.md`. Apply those standards throughout; they override the defaults below. Skip silently when neither file is present.
2. **The user's global coding preferences** in `~/.claude/CLAUDE.md` — already in your context this session. Tests are code, and the naming, docstring, line-width, and idiom rules apply to them.
3. **The surrounding test suite.** Match its idioms — how it parametrizes, names, builds fixtures, and asserts. Local consistency beats personal preference.

When you cite a finding, name which of these it comes from, or state the concrete failure it causes. That keeps the audit honest and lets the user overrule you on the judgment calls.

## Procedure

1. **Establish scope.** Named files if given; otherwise the uncommitted diff, falling back to the tests edited this session. If the scope is too large to audit exhaustively, prioritize and say explicitly what you skipped — a truncated audit that presents itself as complete is worse than a scoped one.
2. **Read the conventions before the tests** (see above), along with the pytest/project config.
3. **Run the suite in scope and note the baseline.** You need to know what's green, what's failing, and what's skipped before you propose anything — a test that's been silently skipped for a year is itself a finding, and post-apply failures have to be attributable.
4. **Read the code under test, not just the tests.** You cannot judge whether a test could catch a real bug, or whether it asserts on an implementation detail, without knowing what the code actually does.
5. **Audit against the axes below.**

## The audit

### Usefulness

Could this test fail for a reason that matters?

- The test has a real chance of catching a bug. If you can't describe a plausible code change that breaks it, it isn't earning its runtime.
- Not testing trivial code that is unlikely to break.
- Not acting as a type checker or linter — asserting a dataclass has the fields it declares, or that a function returns the type it's annotated with, is the checker's job.
- Not testing Python itself or a third-party library: standard container behavior, framework wiring, and a dependency's documented contract are not your suite's responsibility.
- Not tautological: a test that reimplements the function's logic in its assertion passes whatever the function does. Assert against known-good values, invariants, or an independent implementation.
- Weak assertions are a usefulness problem, not a polish one. `assert result is not None`, `assert len(out) > 0`, or a bare "it didn't raise" smoke test rarely fails when the logic breaks — assert on the value, the shape, and the property that actually matters.

### Coverage

The goal is smart and focused, never 100%.

- Obviously correct code paths — input validation, simple pass-through wrappers, `__repr__` — don't need tests.
- Do test domain-specific validation, boundary conditions, and the edge cases where the logic genuinely branches: empty and singleton inputs, zeros and negatives where the math cares, the extremes of a parameter's valid range. These catch real bugs.
- Flag missing regression tests for non-trivial logic, and untested error paths that the code raises deliberately.
- Prefer one parametrized test over five copy-pasted near-identical ones — but only when the cases genuinely share a shape. Parametrizing over cases that need different assertions produces a test with a branch in it, which is worse than two tests.
- Redundant tests that exercise exactly the same path as another test are Remove candidates, even when individually harmless.

### Maintainability

Tests should survive a refactor of the code they cover.

- Tests exercise the *behavior* of the code, not its implementation. Changes to the internals shouldn't require test changes as long as the API contract holds.
- Flag over-mocking: a test that patches the thing it's supposed to be testing, or asserts on call counts and argument tuples rather than outcomes, is pinned to today's implementation and will break on any refactor.
- Flag order-dependence and shared mutable state between tests, unseeded randomness, and dependence on wall-clock time, the network, or filesystem paths outside a tmp fixture. These produce flakes, and a flaky test trains people to ignore failures.
- Assume tests live for years and run millions of times. Weigh each test's value against that cost — an expensive test (large sample, slow fit, big fixture) has to earn its runtime, and often the same bug is caught by a cheaper one.

### Professionalism

A test is documentation of what the code is supposed to do; it should read like it.

- Well written, easy to understand, maximally self-documenting. Descriptive names for test cases and variables — the test name should say what behavior is under test and under what condition, not `test_foo_2`.
- Comments and docstrings only where a future dev needs context they can't get from the code, or where the test does something genuinely non-obvious.
- **Each test reads as one self-contained block.** A reader auditing it should see what was seeded, sampled, patched, and asserted without jumping to a fixture defined hundreds of lines away. Weigh this heavily against DRY: duplicated *setup* (repeated fixture-builder calls, monkeypatch/spy scaffolding, arrange-phase boilerplate) is usually worth keeping inline even at six or eight occurrences, because a fragmented test costs the reader more than the duplication does. **Do not propose extracting it as a cleanup.** This is a strong presumption rather than a prohibition — extraction earns its place when the block is long enough to bury the assertion it sets up, when it encodes an invariant that must stay identical across tests, or when a signature change would otherwise mean editing it everywhere; then keep the call site expressive enough that the test still reads on its own.
- The arrange / act / assert shape should be visible. When the assertion is buried in a wall of setup, that's the case where extraction does pay.

## Output

Group by file. Within each file, sort findings into three tiers:

1. **Remove** — not worth running: trivial, tautological, redundant with another test, or pinned to an implementation detail. Say what coverage is lost (usually none) and why that's acceptable.
2. **Improve** — right intent, poor execution: weak assertions, unclear names, over-mocking, missing parametrization, buried setup.
3. **Add** — a meaningful gap: an untested edge case, an untested deliberate error path, a missing regression test for non-trivial logic.

Format each finding as:

> `path:line` — *the issue in one line* — why it matters (the bug it would miss, or the maintenance it costs) — the concrete change.

Be specific: cite the test function by name. Never suggest a change without justification, and don't pad the report — a finding that doesn't make the suite meaningfully better is clutter.

Close with a two-line summary: counts per tier and the dominant theme.

**In apply mode**, write this report *after* the work, in the past tense, covering what you changed — same tiers, same `path:line` specificity, so the user can audit the diff against it. List anything you held back, with the reason. One report, after the fact; don't emit a proposal-shaped one first.

## Applying fixes

By default, offer to apply, per tier. Under `--apply`, skip the offer and go straight to Improve and Add.

- **Remove** is never bulk-applied, and `--apply` does not change that. Deleting a test destroys coverage, and a test that looks pointless sometimes encodes a bug someone hit in production. Each deletion is a separate proposal the user approves individually.
- **Improve** rewrites must preserve what the test was actually checking. If tightening an assertion makes the test fail, you've found a bug in the code under test — stop and report it rather than weakening the assertion back or "fixing" the source; that's `improve-code` territory and needs the user's decision.
- **Add**ed tests must be run and must pass before you report them. A proposed test that was never executed is a guess. If a new test fails, that's a finding about the code, not a test to quietly drop.

After applying anything, run the suite in scope and compare against the baseline from the procedure. Report the result — including any test that changed from pass to fail, or that you expected to fail and didn't.
