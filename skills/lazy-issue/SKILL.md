---
name: lazy-issue
description: Files a lean, high-signal GitHub issue from a brief bug report or feature request. Use whenever the user mentions a bug, issue, ticket, feature request, or wants to file/report/open something -- even if they don't say "issue" explicitly.
disable-model-invocation: true
---

# lazy-issue

File a GitHub issue a busy maintainer will actually read. Same philosophy as `lazy-pr`: less is more. A one-sentence problem statement plus a repro they can paste beats three screens of prose. Long, sectioned, heading-heavy issues read as LLM filler and get skimmed past -- the effort actively works against you. Your job here is to strip, not to pad.

## Input

$ARGUMENTS

## Available labels

!`gh label list --json name,description --limit 100`

## First, how many problems is this?

An issue is closed when its problem is fixed, so two problems in one issue can never be closed cleanly -- the maintainer fixes one and the thread lives on with a half-done second thing buried in it. If you are about to describe a second symptom with a different cause, that is a second issue. Draft both and say so; let the user decide whether to file one or two.

A second symptom the *same* cause produces is the opposite case. That stays in the one issue and usually in the one sentence, because it is evidence about a single problem rather than a second problem.

This is where an issue and a PR part company. In `lazy-pr` a genuinely separate change earns its own paragraph in the same description. Here it earns its own issue, because the unit being closed is the problem, not the work.

## The format

A good issue is three things and nothing else. A title under 80 chars that names the symptom and, if it fits, the cause -- `pm.sample segfaults on Apple Silicon: fork default + Accelerate BLAS`, not `Bug in sampling`. A short paragraph saying what breaks and why. And a code block: for a bug, a complete runnable MWE, with the workaround as a trailing comment in the code rather than as prose.

The paragraph is built in a fixed order. The first sentence states what breaks, using the real identifier and saying what kind of thing it is: `pm.sample` is a function, `Courts of Otosan Uchi` is a card, `load_cards` is the loader. A maintainer who has never opened this repo reads that sentence and knows what the issue is about. The second sentence says why, if you know why. If you don't, say what you observed and stop. Cause never precedes symptom, and a sentence that opens on a mechanism whose symptom has not appeared yet is out of order.

One sentence carries one claim. No em-dashes. No colons joining two independent clauses. A sentence has at most one subordinate clause. If the because, the so, and the but need more room, they get their own sentence. The paragraph is two or three sentences, and a third exists only to carry a consequence the maintainer needs before opening the MWE.

That is the entire body, with one addition that earns its way in: a number you actually measured. A timing, a wrong value next to the right one, a rate. Those are the one thing a maintainer can neither derive from the MWE nor take on trust, and an issue that has them should keep them even when that makes it the longest one you file. No `Description`, `Analysis`, `Severity`, `Steps to Reproduce`, `Expected vs Actual`, or `What needs to be done` headings. No emoji section markers, no bolded key-phrases, no bullet inventories of files or symbols. If a fact doesn't fit in the paragraph and isn't visible in the MWE, it's probably not worth saying.

Don't gather permalinks to decorate a diagnosis -- the maintainer can find the code. The exception is when the exact lines *are* the request: a one-line annotation fix or a constant that's wrong is clearest as a link straight to it, and then the link replaces the explanation rather than padding it.

Example body:

> `pm.sample` segfaults in every chain worker on Apple Silicon once the model is large enough to hit a threaded BLAS path. The default `mp_ctx="fork"` is the cause. conda's numpy now links Apple Accelerate, and Accelerate's worker threads don't survive `fork()`.
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

Laziness belongs in the prose, not the evidence. Before posting a bug, write the smallest self-contained script that triggers it and **run it** to confirm it fails. A repro the maintainer can paste and watch break is the single highest-signal thing in the issue -- it earns the effort that prose doesn't. Reduce it to the minimum: only what's needed to trigger the bug, standard library and project dependencies only.

If the failure is a clean Python traceback and it's long, tuck it under a collapsed `<details><summary>traceback</summary>` block beneath the code. For a segfault, hang, or wrong-number bug, skip that -- say so in the sentence and let the MWE speak.

If a bug genuinely can't be reduced to a runnable script (flaky, visual, environment-specific), don't fake one: give the one sentence plus the shortest concrete steps to see it, and note that it isn't reliably reproducible. Still no headings. That issue is shorter than a normal one, not longer -- the absence of a repro is not a reason to compensate with prose.

Example, no repro available:

> The Windows CI job for `test_parallel_paths_match_serial_per_path` fails about one run in four with a worker timeout. Passes locally on Windows every time, never failed on Linux or macOS. No reliable repro; rerunning the job is the only way I've found to see it.

## Features, not bugs

Same discipline: one sentence on what you want, one on why it's worth doing, and -- only if it clarifies -- a short code block showing the desired API or call site as you'd want it to read. No MWE to run, no roadmap, no deliverables list, no sketch of the implementation, no inventory of the files it would touch. There is no repro to earn effort here, so a feature request is the shortest thing this skill produces, not a license to argue the case at length.

Example:

> `build_client` should expose the config it resolved to. It takes a retry policy today but gives no way to read it back, so debugging a misconfigured client means reading the constructor. An accessor would do it:
>
> ```python
> client = build_client(retry_policy="exponential")
> client.effective_config  # {"retry_policy": "exponential", "timeout_s": 30, ...}
> ```

And a feature whose API is obvious needs no code block at all:

> `find_MAP` returns a `DataTree` but its annotation still says `dict`, so editors autocomplete the wrong thing.

## Voice

Write for a maintainer who has never opened this repo and is reading in a hurry. Contractions are fine. Plain declarative sentences are the goal. No sentence fragments.

American English, always. British spellings in an issue body are an instant tell.

Name code by its identifier, then say in plain words what kind of thing it is. Never substitute a description you coined for a name that exists.

No figurative verbs for what code does. Code does not bite, walk, reach across, go live, sit below, or leak. It calls, reads, imports, returns, raises, and drops.

Skip the technical-report register. If a phrase would sound stilted said out loud, it's wrong here. No hedging a diagnosis you're confident in, no apologizing for filing, no announcing what the issue is about before saying it ("this issue reports...").

Plain register is not permission to be cute. Never soften a real technical consequence with diminishing or jokey framing -- "one wrinkle", "small gotcha", "fun catch", "worth noting though". And never signpost instead of stating -- "worth doing properly", "blast radius", "where it lives", "one decision first". A caveat that changes behavior, breaks an invariant, or needs a maintainer's decision is stated flatly as what it is: name the thing that breaks and what it forces. If it's important enough to include, it's important enough to say straight.

## What to leave out

One test, applied to every clause: could the maintainer get this from the title and the MWE? If yes, cut it.

That test has a hole, and it matters more here than the same test does in `lazy-pr`. The MWE shows the symptom; it never shows the cause. So the cause is the one thing the test can never license cutting, and a sentence that only restates what the reader is about to watch happen is a caption, not an issue. If you know why it breaks, that is what the second sentence is for. If you don't know, say what you observed and don't invent one.

The test bounds detail, never the first sentence. The symptom sentence is always derivable from the MWE, and it stays anyway, because a maintainer opening a fresh issue has your paragraph and your script and nothing else. Opening on a private helper or an internal term as though it were shared context fails that reader completely.

Past that, the test does most of the work, but it's easy to pass in spirit and fail in practice, because detail you just spent an hour on feels load-bearing when it isn't. Check the draft against each of these by name:

- Enumeration the prose doesn't need. Exact line numbers, enumerated call chains, version matrices, lists of the files involved. Let the MWE supply the specifics. This licenses cutting lists, never replacing an identifier with a description you invented. Name a version only when the bug is version-dependent.
- The story of the debugging. How you found the cause, what you ruled out, what you tried first. The most tempting material and the least useful; it belongs in chat. A mechanism is not story when it explains a symptom already stated on the page. It is story when it stands in for that statement.
- Arguing for the fix. A short proposed fix is welcome and often the most useful thing in the issue, but it belongs in a code block under a plain `Potential fix (requires testing):` line, not in prose, and it stops there. The moment it becomes a case for an approach, weighing alternatives or pre-empting the design, it is the PR's content and it goes in the PR.
- Severity theater. "Critical", "blocking", "urgent", "this should be prioritized". Triage is the maintainer's job and they are better at it than you are; state what breaks and let the facts carry it.
- A sentence that restates the title. If the title already says the symptom, the second sentence exists to add the cause. If it can't, the issue is a title and an MWE, and that is a complete issue.
- A justification with no antecedent. A sentence that explains why, when the what has not appeared yet. Move the what in front of it.
- A coined phrase where an identifier belongs. "The escape guard", "the set-file walk", "the sandbox surface", when the code has a name. Use the name, then say what kind of thing it is.

A body that fails the test:

> While tracing this I found that `_build_config` at `src/rx/config/loader.py:88` shallow-copies the options dict before the decorator merges defaults, so any key set by the caller after import time is silently discarded. I checked and this affects `retry_policy`, `timeout_s`, and `backoff_factor` on both 0.14.2 and 0.15.0. A deep merge would fix it, though a targeted fix to just `retry_policy` is also possible -- happy to open a PR either way.

The same issue:

> `build_client` ignores `retry_policy` and any other option the caller sets. `_build_config` shallow-copies the options dict before the defaults merge, so caller-set keys are dropped.
>
> ```python
> from rx.config import build_client
>
> client = build_client(retry_policy="exponential")
> print(client.retry_policy)  # "none"
> ```

Cause first, then the same issue with the symptom first:

> `Resolver` types `source_id` as `str | None` because the rulebook's Cycle raises its `Choose` without a source, but 25 of the 29 registered resolvers declare it as plain `str`. Narrowing a parameter breaks contravariance, so every one of them is an invalid `Resolver` -- `basedpyright` reports 25 errors across `rules/cards/`. Nothing bites today only because each of those resolvers happens to be reached from decisions that always carry a source, which nothing enforces and no signature records.

> 25 of the 29 registered choice resolvers fail type checking, because they declare `source_id: str` where the `Resolver` protocol says `str | None`. `basedpyright` reports one error per resolver across `rules/cards/`. Nothing fails at runtime today, because every one of those resolvers is only reached from decisions that carry a source, and nothing enforces that.

## Explore only as far as the sentence needs

Read the code enough to write an accurate one-sentence cause and a correct MWE, and no further. You're not producing a root-cause report; you're handing a maintainer a true, tight starting point. Don't gather permalinks or line references you won't use.

## Submit

**Always show the full draft and get explicit authorization before posting. Never run `gh issue create` on your own initiative.** Posting is public and hard to walk back -- a wrong label, a typo'd title, or a half-baked repro is out there the moment the command runs, so the user makes the call to publish, every time. This holds even if the user said "file an issue" up front: that's the request to *draft* one; it is not standing permission to post. It holds even when you're confident the draft is perfect.

So the flow is:

1. Pick labels from the list above -- only those that genuinely apply.
2. Show the user the complete draft exactly as it will appear: title, chosen labels, and the rendered body (sentence + code block). Then ask whether to post, or whether they want changes.
3. Wait for an explicit go-ahead ("post it", "yes", "ship it", or similar). Anything short of that -- silence, a question, a tweak -- means don't post yet. If they only want changes, revise and show the draft again.
4. Only then run:

   ```
   gh issue create --title "<title>" --label "<label>" --label "<label>" --body-file <file>
   ```

   Write the body to a file and pass `--body-file` so code fences and newlines survive intact.
5. Show the user the returned URL.

Don't append a separate analysis write-up to the issue afterward -- if you learned something useful while reducing the repro, say it in a sentence in chat, not in the ticket.
