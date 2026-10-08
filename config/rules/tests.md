---
paths:
  - "**/tests/**"
  - "**/test_*.py"
---

# Tests

Test behavior that has a plausible failure mode. One-line changes, version pins, config entries, pass-through wiring, and scripts under `scripts/` or `audits/` get no tests, because the run that needed them is the verification.

Do not compare a refactored function against a pinned copy of its old body. The existing behavior tests already cover the refactor.

Keep setup inline so each test reads as one block, even when a few lines repeat across tests. Extract a fixture only when setup buries the assertion, encodes an invariant every test must share, or would need editing everywhere on a signature change.

Speed up a slow suite by cutting total work (wider fixture scope, fewer draws, deleting redundant tests). Do not tune xdist scheduling or benchmark wall-clock across worker settings.

When mutation-testing, revert the mutation with the inverse edit. Never `git checkout` or `git restore` a file that has uncommitted work.
