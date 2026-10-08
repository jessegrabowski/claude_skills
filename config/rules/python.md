---
paths:
  - "**/*.py"
---

# Python Source

Docstrings are either a one-line summary or a full numpy-sectioned docstring, nothing in between. No `Raises` or `Warns` sections. Every `Returns` entry gets a name (`idata : az.InferenceData`), and a function that returns None has no `Returns` section. Types are human-readable (`list of str`, `pd.DataFrame or None`, `{"call", "put"}`), not annotations. Summaries use the imperative ("Fit the curve"). State the contract and leave out recipes for how a caller might satisfy it.

No module docstrings on source or test modules. Package `__init__.py` docstrings are fine.

Do not add `from __future__ import annotations`. It exists to break circular typehint imports, and these repos have none.

Do not add `typing.cast` to appease a type checker. Add pyright directives only in repos with a `[tool.basedpyright]` section. Elsewhere, leave false positives alone.
