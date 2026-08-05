---
name: improve-tests
description: Quality and coverage audit of test files. Use when the user asks to improve tests, review test quality, audit test coverage, or professionalize tests.
---

You will perform a quality and coverage assessment of the tests of the files requested in the arguments. If no files are specified, focus only on the tests that are currently being worked on. Ask for further clarification if there are no obvious candidates.


## Input 

$ARGUMENTS

## Instructions

### Usefuless

- Tests have a real chance of catching a bug in the code.
- Tests are not testing trivial code that is unlikely to break.
- Tests are not type checkers or linters.
- Tests are not testing the test framework itself.

### Professionalism
- Tests are well written and easy to understand.
- Tests are maximally self-documenting and use descriptive names for test cases and variables.
- Comments and docstrings are used only in rare cases where future devs need additional context, or where the test is doing something non-obvious that future devs might not understand.
- Each test reads as one self-contained block. A reader auditing it should see what was seeded, sampled, patched, and asserted without jumping to a fixture defined hundreds of lines away. Weigh this heavily against DRY: duplicated *setup* (repeated fixture-builder calls, monkeypatch/spy scaffolding, arrange-phase boilerplate) is usually worth keeping inline even at six or eight occurrences, because a fragmented test costs the reader more than the duplication does. Do not propose extracting it as a cleanup. This is a strong presumption rather than a prohibition — extraction earns its place when the block is long enough to bury the assertion it sets up, when it encodes an invariant that must stay identical across tests, or when a signature change would otherwise mean editing it everywhere; then keep the call site expressive enough that the test still reads on its own.

### Coverage
- The goal of the tests is not 100% coverage.
- Tests are smart and focused.
- Obviously correct code paths, like input validation, are not tested.

### Maintainability
- Tests test *behavior* of the code, not implementation details.
- Changes to the underlying routines being exercised do not require changes to the tests (provided the api contract does not change).
- Assume tests will be live for years, and run millions of time. Weigh the usefulness of the test against the C02 emissions that implies.

