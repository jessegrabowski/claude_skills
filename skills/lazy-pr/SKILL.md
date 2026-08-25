---
name: lazy-pr
description: Opens a lean, high-signal GitHub pull request from the current branch, after the required quality passes have run. Use whenever the user wants to open, raise, submit, or draft a PR.
disable-model-invocation: true
---

# lazy-pr

Open a pull request a reviewer will actually read. Same philosophy as `lazy-issue`: less is more. Say what changed and why, then get out of the way. The diff is the content; the description is a pointer to it. Headings, bullet inventories, "Summary / Changes / Testing / Impact" scaffolding, emoji section markers, and bolded key-phrases read as machine filler and make the author look like they didn't read their own diff. Strip, don't pad.

## Input

$ARGUMENTS

## Gate: the quality passes must have run first

Before drafting anything, confirm that all three of these ran against the work in this PR, in this conversation:

1. `improve-code`
2. `improve-tests`
3. `split-and-commit`

Check the conversation history, not your memory of intent. Evidence that a pass ran means the skill was actually invoked and its changes landed -- not that the code "looks fine" or that you were careful while writing it.

If any of the three is missing, say which ones and run them now, in that order, before continuing.

Run the missing audits with `--apply` -- `improve-code --apply`, `improve-tests --apply`. The gate exists to get the branch into shape, and a findings report the user has to adjudicate tier by tier stalls the PR they just asked for. `--apply` lands the behavior-preserving work directly and reports it afterward.

Both skills hold back their destructive tier even under `--apply`: `improve-code` still proposes each bug fix individually, and `improve-tests` still proposes each test deletion. Those come back to the user as questions. Answer them before drafting -- a PR opened over an unresolved bug finding is worse than a slow one.

`improve-code` and `improve-tests` produce edits, so they must precede `split-and-commit`; if either one lands changes after commits were made, `split-and-commit` runs again for the new work. Do not open a PR with an uncommitted working tree.

If the user explicitly tells you to skip a pass, say once that you're skipping it and proceed. Their call.

## The title

Under 72 chars, imperative, specific. Names the change, not the activity: `Cache curve bootstrap results per settlement date`, not `Improvements to bootstrapping` or `feat: various fixes`. If the repo's PR history uses a prefix convention (`[area]`, `feat:`), match it.

## The body

Start with scope, not length. How many changes is this PR? Not how many commits, and not how many true things you could say -- how many changes a reviewer would form a separate opinion about.

Almost always the answer is one, and one change is one paragraph. Everything that serves that change belongs inside it, however separate the work felt while you were doing it: a restriction lifted so the main rewrite can fire, a helper widened so the new path has something to call, a test reworked around the new behavior. Those are parts of the change. Giving one its own paragraph tells the reviewer to weigh it on its own, which is the wrong instruction.

So a second paragraph is one more change, never one more fact about the same change. An unrelated fix made while passing through earns one. A consequence, a caveat, a carve-out, or a mechanism does not -- those go in the paragraph of the change they belong to, or they get cut. This is the rule most likely to be violated without noticing, because the second paragraph always contains something true.

Then, within the paragraph, draft the one-sentence version first. Write it out before deciding anything about length -- not as a thought experiment, as actual text on the page.

For every further sentence you want to add, apply one test: would a reviewer who has read the diff still not know this? Not "would they find it useful", not "does it add context" -- would they not know it.

Most bodies pass that test at one sentence. Many pass at two. If a third sentence passes, one of the three is really failing, so go find which one. The count is a diagnostic, not a budget: there is no length you are expected to reach, and a body that is nothing but `Closes #412` is a finished body.

The test bounds detail, not comprehension. It licenses cutting specifics the diff supplies. It never licenses cutting the sentence that makes the rest legible to a reviewer reading cold, without the domain loaded. A body that only parses once you already know what the change does has failed at the one job it has, and the fix is one orienting sentence at the front, in plain terms, before anything specific.

Three lines attach independently of that count, each only when it applies:

- `Closes #123` / `Fixes #123`, when there's an issue
- a short code block, when a call site or API shape is the clearest way to show the change
- one line on how it was verified, when verification was non-obvious -- new test file names don't need saying, they're in the diff

Keep the one-sentence version. When you show the draft, put it above the body you propose, labeled, with one line on what the rest of the body says that it doesn't. Judging your own draft in the abstract is nearly free, and it always comes back justified; having to display the version you threw away, next to your reason for throwing it away, is what makes the choice real. It also hands the user the shorter option to accept in one word.

That's the whole body. No section headings. No file-by-file walkthrough. No bulleted list restating each commit; the commit log exists and is one click away. No "this PR..." preamble -- start with the substance.

## Examples

A body that is only a link, where the title already carries the change:

> Closes #488

One sentence:

> `spread_to_price` silently returned NaN for callable bonds with a past next-call date; now raises instead of poisoning downstream aggregates.

Two, where the second says something the diff doesn't:

> Curve bootstrapping re-ran for every bond in a batch even when they shared a settlement date, which dominated runtime on the 40k-bond nightly job. Now keyed on settlement date and memoized for the life of the call.
>
> Closes #412

Padded, then the same PR after the test:

> The `retry_policy` argument was being dropped because `_build_config` shallow-copies the options dict at line 88 before the decorator merges defaults, so any key set by the caller after import time was silently discarded. This affected `retry_policy`, `timeout_s`, and `backoff_factor`. Changed the shallow copy to a deep merge, which is behavior-preserving for every other key -- a targeted fix to just `retry_policy` was possible but would leave the same bug latent for the other two, so the broader fix was taken.

> Caller-set options were silently dropped when they landed after the defaults merge. `_build_config` now deep-merges instead of shallow-copying.

Cut past sense, then the same PR made readable cold:

> `spread_to_price` was collecting on stub periods too -- which the day-count convention treats as accrual, not a payment.

> Nothing distinguished a real coupon from an accrual stub, so `spread_to_price` counted both as payments. Under the day-count convention a stub accrues rather than pays, so callable bonds with a short first period priced high.

## Read the draft against these

Named failure modes. Check the draft against each one by name before showing it.

- Ticket paraphrase. The body restates the linked issue in different words. The issue is one click away and adds nothing here.
- The story of the work. How you found the cause, what the mechanism turned out to be, what you tried first, what you decided against and why. The most tempting material and the least useful; it belongs in chat, or in a follow-up issue if something is genuinely left undone.
- Precision the prose doesn't need. Exact versions, full symbol paths, enumerated renames, file counts. If a category-level phrase covers it, use the category and let the diff supply the specifics.
- Unfalsifiable adjectives. "Cleaner", "more robust", "improved performance", with nothing a reviewer can check. Measure it or cut it.
- Verification theater. "Tested thoroughly." Name what was checked and why it was non-obvious, or say nothing.
- Opening on a proper noun the reader has to go look up. A card, a class, a config key, a customer -- named in the first clause as though it were shared context. Say what kind of thing it is and what went wrong with it, then name it.
- Three ideas stacked into one sentence, joined by em-dashes, each one load-bearing. Split them. Short declarative sentences are not less sophisticated; they are the ones that survive being read in a hurry.

The trivial PR is where padding is worst. With nothing much to say, the pull is to manufacture something -- restating the title, narrating the process, inflating a one-line fix into a paragraph. A one-line body on a one-line change is the correct output, not a failure to try harder.

## Voice

Write like you're telling a colleague what you did, in a hurry, from your phone. Contractions are fine. Sentence fragments are fine. Naming the thing plainly and stopping is the goal.

American English, always. British spellings in a PR body are an instant tell.

Skip the technical-report register. If a phrase would sound stilted said out loud, it's wrong here. No hedging a decision you already made, no defending one nobody questioned, no announcing what the change does before doing it ("this PR introduces...").

Casual register is not permission to be cute. Never soften a real technical consequence with diminishing or jokey framing -- "one wrinkle", "small gotcha", "fun catch", "worth noting though". And never signpost a hazard instead of stating it -- "worth a close look", "the interesting bit", "keep an eye on", "one thing to watch", "heads up". That phrasing promises significance and makes the reviewer go find it; name the hazard directly, so they read the consequence before they read the diff. A caveat that changes behavior, breaks an invariant, or needs the reviewer's decision is stated flatly as what it is. If it's important enough to include, it's important enough to say straight.

## Commits

Commit messages follow `split-and-commit`: imperative mood, one line, <= 79 chars, matching repo conventions. No Claude attribution anywhere -- no `Co-Authored-By: Claude...`, no `Generated with...`, in commits or in the PR body. If a commit already carries attribution from an earlier turn and hasn't been pushed, offer to rewrite it; don't rewrite published history on your own.

## Branch and push

- If the work is on the default branch (`main`/`master`), stop and ask before creating a branch or moving commits. Don't unilaterally restructure where their commits live.
- Push with `git push -u origin <branch>`. Never force-push. Never `--no-verify`.
- Pushing is the point of no return for CI and for anyone watching the repo, so it happens as part of the authorized submit flow below, not ahead of it.

## Submit

**Always show the full draft and get explicit authorization before pushing or running `gh pr create`.** A PR notifies reviewers and kicks off CI the moment it opens; a wrong base branch or a half-baked title is out there immediately. The user makes the call, every time. "Open a PR" is the request to *draft* one -- it is not standing permission to publish. This holds even when you're confident the draft is perfect.

The flow:

1. Confirm the gate above is satisfied and the working tree is clean.
2. Check the base branch (`gh repo view --json defaultBranchRef`) and the commits that will ship (`git log <base>..HEAD --oneline`).
3. Show the user the complete draft exactly as it will appear: title, base branch, commit list, and the rendered body -- preceded by the one-sentence version and why the body goes past it. Ask whether to open it, or whether they want changes.
4. Wait for an explicit go-ahead ("open it", "yes", "ship it", or similar). Silence, a question, or a tweak means don't publish yet -- revise and show the draft again.
5. Only then push, and run:

   ```
   gh pr create --base <base> --title "<title>" --body-file <file>
   ```

   Write the body to a file and pass `--body-file` so newlines and code fences survive. Add `--draft` if the user asked for a draft PR.
6. Show the returned URL.

Don't post a follow-up comment expanding on the description. If you learned something worth saying while doing the work, say it in chat.
