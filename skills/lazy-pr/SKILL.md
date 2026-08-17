---
name: lazy-pr
description: Opens a lean, high-signal GitHub pull request from the current branch, after the required quality passes have run. Use whenever the user wants to open, raise, submit, or draft a PR.
disable-model-invocation: true
---

# lazy-pr

Open a pull request a reviewer will actually read. Same philosophy as `lazy-issue`: **less is more**. One or two sentences on what changed and why, and then get out of the way. The diff is the content; the description is a pointer to it. Headings, bullet inventories, "Summary / Changes / Testing / Impact" scaffolding, emoji section markers, and bolded key-phrases read as machine filler and make the author look like they didn't read their own diff. Strip, don't pad.

## Input

$ARGUMENTS

## Gate: the quality passes must have run first

Before drafting anything, confirm that all three of these ran against the work in this PR, in this conversation:

1. `improve-code`
2. `improve-tests`
3. `split-and-commit`

Check the conversation history, not your memory of intent. Evidence that a pass ran means the skill was actually invoked and its changes landed -- not that the code "looks fine" or that you were careful while writing it.

If any of the three is missing, say which ones and run them now, in that order, before continuing.

**Run the missing audits with `--apply`** -- `improve-code --apply`, `improve-tests --apply`. The gate exists to get the branch into shape, and a findings report the user has to adjudicate tier by tier stalls the PR they just asked for. `--apply` lands the behavior-preserving work directly and reports it afterward.

Both skills hold back their destructive tier even under `--apply`: `improve-code` still proposes each bug fix individually, and `improve-tests` still proposes each test deletion. Those come back to the user as questions. Answer them before drafting -- a PR opened over an unresolved bug finding is worse than a slow one.

`improve-code` and `improve-tests` produce edits, so they must precede `split-and-commit`; if either one lands changes after commits were made, `split-and-commit` runs again for the new work. Do not open a PR with an uncommitted working tree.

If the user explicitly tells you to skip a pass, say once that you're skipping it and proceed. Their call.

## The format

**Title** -- under 72 chars, imperative, specific. Names the change, not the activity: `Cache curve bootstrap results per settlement date`, not `Improvements to bootstrapping` or `feat: various fixes`. If the repo's PR history uses a prefix convention (`[area]`, `feat:`), match it.

**Body** -- one paragraph. Two or three sentences, one is often enough. What changed, and the why that isn't obvious from the diff. Then, only if they apply:

- a `Closes #123` / `Fixes #123` line, when there's an issue
- a short code block, when a call site or API shape is the clearest way to show the change
- one line on how it was verified, when verification was non-obvious (new test file names don't need saying -- they're in the diff)

That's the whole body. No section headings. No file-by-file walkthrough. No bulleted list restating each commit -- the commit log already exists and is one click away. No "this PR..." preamble; start with the substance.

**Example body:**

> Curve bootstrapping re-ran for every bond in a batch even when they shared a settlement date, which dominated runtime on the 40k-bond nightly job. Now keyed on settlement date and memoized for the life of the call.
>
> Closes #412

**Also fine, for a small change:**

> `spread_to_price` silently returned NaN for callable bonds with a past next-call date; now raises instead of poisoning downstream aggregates.

## Voice

Write like you're telling a colleague what you did, in a hurry, from your phone. Contractions are fine. Sentence fragments are fine. Naming the thing plainly and stopping is the goal.

**American English. Always.** British spellings in a PR body are an instant tell.

Skip the technical-report register. If a phrase would sound stilted said out loud, it's wrong here. No hedging a decision you already made, no defending one nobody questioned, no announcing what the change does before doing it ("this PR introduces...").

Casual register is not permission to be cute. Never soften a real technical consequence with diminishing or jokey framing -- "one wrinkle", "small gotcha", "fun catch", "worth noting though". And never signpost a hazard instead of stating it -- "worth a close look", "the interesting bit", "keep an eye on", "one thing to watch", "heads up". That phrasing promises significance and makes the reviewer go find it; name the hazard directly, so they read the consequence before they read the diff. A caveat that changes behavior, breaks an invariant, or needs the reviewer's decision is stated flatly as what it is. If it's important enough to include, it's important enough to say straight.

## What to leave out

One test, applied to every clause: **could the reviewer get this from the diff?** If yes, cut it. The body exists to tell them why to look and what to watch for -- nothing else.

That test does most of the work, but it's easy to pass in spirit and fail in practice, because detail you just spent an hour on feels load-bearing when it isn't. Two habits to watch for:

- **Precision the prose doesn't need.** Exact versions, full symbol paths, enumerated renames, file counts. If a category-level phrase covers it, use the category and let the diff supply the specifics.
- **The story of the work.** How you found the cause, what the underlying mechanism turned out to be, what you tried first, what you decided against and why. This is the most tempting material and the least useful; it belongs in chat, or in a follow-up issue if something is genuinely left undone.

Verification is assumed. Mention it only when it's surprising.

**A body that fails the test:**

> The `retry_policy` argument was being dropped because `_build_config` shallow-copies the options dict at line 88 before the decorator merges defaults, so any key set by the caller after import time was silently discarded. This affected `retry_policy`, `timeout_s`, and `backoff_factor`. Changed the shallow copy to a deep merge, which is behavior-preserving for every other key -- a targeted fix to just `retry_policy` was possible but would leave the same bug latent for the other two, so the broader fix was taken.

**The same PR:**

> Caller-set options were silently dropped when they landed after the defaults merge. `_build_config` now deep-merges instead of shallow-copying.

## Commits

Commit messages follow `split-and-commit`: imperative mood, one line, <= 79 chars, matching repo conventions. **No Claude attribution anywhere** -- no `Co-Authored-By: Claude...`, no `🤖 Generated with...`, in commits or in the PR body. If a commit already carries attribution from an earlier turn and hasn't been pushed, offer to rewrite it; don't rewrite published history on your own.

## Branch and push

- If the work is on the default branch (`main`/`master`), stop and ask before creating a branch or moving commits. Don't unilaterally restructure where their commits live.
- Push with `git push -u origin <branch>`. Never force-push. Never `--no-verify`.
- Pushing is the point of no return for CI and for anyone watching the repo, so it happens as part of the authorized submit flow below, not ahead of it.

## Submit

**Always show the full draft and get explicit authorization before pushing or running `gh pr create`.** A PR notifies reviewers and kicks off CI the moment it opens; a wrong base branch or a half-baked title is out there immediately. The user makes the call, every time. "Open a PR" is the request to *draft* one -- it is not standing permission to publish. This holds even when you're confident the draft is perfect.

The flow:

1. Confirm the gate above is satisfied and the working tree is clean.
2. Check the base branch (`gh repo view --json defaultBranchRef`) and the commits that will ship (`git log <base>..HEAD --oneline`).
3. Show the user the complete draft exactly as it will appear: title, base branch, commit list, and the rendered body. Ask whether to open it, or whether they want changes.
4. Wait for an explicit go-ahead ("open it", "yes", "ship it", or similar). Silence, a question, or a tweak means don't publish yet -- revise and show the draft again.
5. Only then push, and run:

   ```
   gh pr create --base <base> --title "<title>" --body-file <file>
   ```

   Write the body to a file and pass `--body-file` so newlines and code fences survive. Add `--draft` if the user asked for a draft PR.
6. Show the returned URL.

Don't post a follow-up comment expanding on the description. If you learned something worth saying while doing the work, say it in chat.
