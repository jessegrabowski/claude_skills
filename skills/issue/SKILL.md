---
name: issue
description: Files a lean, high-signal GitHub issue from a brief bug report or feature request. Use whenever the user mentions a bug, issue, ticket, feature request, or wants to file/report/open something — even if they don't say "issue" explicitly.
disable-model-invocation: true
---

# issue

File a GitHub issue a busy maintainer will actually read. The whole philosophy is **less is more**: a one-sentence problem statement plus a repro they can paste beats three screens of prose. Long, sectioned, heading-heavy issues read as LLM filler and get skimmed past — the effort actively works against you. Your job here is to strip, not to pad.

## Input

$ARGUMENTS

## Available labels

!`gh label list --json name,description --limit 100`

## The format

A good issue is three things and nothing else:

1. **Title** — under 80 chars, specific. Name the symptom and, if it fits, the cause: `pm.sample segfaults on Apple Silicon: fork default + Accelerate BLAS`, not `Bug in sampling`.
2. **One sentence** — what breaks and why, in a single tweet-length sentence. If you reach for a second sentence, it's usually restating the first; cut it.
3. **A code block** — for a bug, a complete, runnable MWE. Put the workaround, if there is one, as a trailing comment in the code rather than as prose.

That is the entire body. No `Description`, `Analysis`, `Severity`, `Steps to Reproduce`, `Expected vs Actual`, or `What needs to be done` headings. No permalinks. If a fact doesn't fit in the sentence and isn't visible in the MWE, it's probably not worth saying.

**Example body:**

> On Apple Silicon `pm.sample` defaults to `mp_ctx="fork"`, but conda's numpy now links Apple Accelerate whose worker threads don't survive `fork()`, so any model large enough to hit Accelerate's threaded BLAS path segfaults every chain worker.
>
> ```python
> import numpy as np
> import pymc as pm
>
> N = 500_000  # large enough that X @ beta hits Accelerate's threaded BLAS path
> X = np.random.default_rng(0).normal(size=(N, 10))
> y = X @ np.arange(10.0) + np.random.default_rng(1).normal(size=N)
>
> with pm.Model() as model:
>     beta = pm.Normal("beta", shape=10)
>     pm.Normal("y", mu=X @ beta, sigma=1.0, observed=y)
>     pm.sample(draws=100, tune=100, chains=2, cores=2)  # workers die -> EOFError
>     # workaround: pm.sample(..., mp_ctx="spawn")
> ```

## The one bit of real work: make the MWE actually reproduce

Laziness belongs in the prose, not the evidence. Before posting a bug, write the smallest self-contained script that triggers it and **run it** to confirm it fails. A repro the maintainer can paste and watch break is the single highest-signal thing in the issue — it earns the effort that prose doesn't. Reduce it to the minimum: only what's needed to trigger the bug, standard library and project dependencies only.

If the failure is a clean Python traceback and it's long, tuck it under a collapsed `<details><summary>traceback</summary>` block beneath the code. For a segfault, hang, or wrong-number bug, skip that — say so in the sentence and let the MWE speak.

If a bug genuinely can't be reduced to a runnable script (flaky, visual, environment-specific), don't fake one: give the one sentence plus the shortest concrete steps to see it, and note that it isn't reliably reproducible. Still no headings.

## Features, not bugs

Same discipline: one sentence on what you want and why it's worth doing, and — only if it clarifies — a short code block showing the desired API or call site as you'd want it to read. No MWE to run, no roadmap, no deliverables list.

## Explore only as far as the sentence needs

Read the code enough to write an accurate one-sentence cause and a correct MWE, and no further. You're not producing a root-cause report; you're handing a maintainer a true, tight starting point. Don't gather permalinks or line references you won't use.

## Submit

**Always show the full draft and get explicit authorization before posting. Never run `gh issue create` on your own initiative.** Posting is public and hard to walk back — a wrong label, a typo'd title, or a half-baked repro is out there the moment the command runs, so the user makes the call to publish, every time. This holds even if the user said "file an issue" up front: that's the request to *draft* one; it is not standing permission to post. It holds even when you're confident the draft is perfect.

So the flow is:

1. Pick labels from the list above — only those that genuinely apply.
2. Show the user the complete draft exactly as it will appear: title, chosen labels, and the rendered body (sentence + code block). Then ask whether to post, or whether they want changes.
3. Wait for an explicit go-ahead ("post it", "yes", "ship it", or similar). Anything short of that — silence, a question, a tweak — means don't post yet. If they only want changes, revise and show the draft again.
4. Only then run:

   ```
   gh issue create --title "<title>" --label "<label>" --label "<label>" --body-file <file>
   ```

   Write the body to a file and pass `--body-file` so code fences and newlines survive intact.
5. Show the user the returned URL.

Don't append a separate analysis write-up to the issue afterward — if you learned something useful while reducing the repro, say it in a sentence in chat, not in the ticket.
