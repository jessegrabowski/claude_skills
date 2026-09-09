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

Start with scope. How many changes is this PR? Not how many commits, and not how many true things you could say -- how many changes a reviewer would form a separate opinion about. Almost always the answer is one.

Each change gets a paragraph, and the paragraph is built in a fixed order.

The first sentence states what changed, in plain terms, using the real identifiers: `X now does Y`, `X moved from A to B`, `Added X`, `Removed X`. It names the code by its identifier and then says what kind of thing that identifier is, so a reviewer who has never opened the repo can follow. This sentence is never cut on the grounds that the diff already shows it. The diff shows it to someone who has read the diff, and the body exists for the reviewer deciding whether to.

Sentences after the first say why, and only when the why is not obvious from the change itself. Rationale never precedes the fact it explains. If a sentence begins with a reason, a mechanism, or a description of the world before the change, and the change it belongs to has not yet appeared on the page, the sentence is out of order.

One sentence carries one claim. No em-dashes. No colons joining two independent clauses. A sentence has at most one subordinate clause, and if the because, the so, and the but need more room than that, they get their own sentence. Terseness comes from cutting content, never from cutting the words that carry logic.

A paragraph is two or three sentences. If the change needs more, the extra material is a caveat, a carve-out, or a consequence, and it gets a second paragraph of its own. That paragraph opens by naming what it is a caveat to: `AttackEffect stays in effects.py.` is a legitimate opener. What it may not do is read as an independent change when it is one. The opener carries that distinction, not the paragraph count.

A paragraph never opens with a connective that points at something not yet on the page: `otherwise`, `separately`, `also`, `that's what lets`, `which is why`. Those words only appear when the writer has stated the exception before the rule, and the fix is to state the rule first.

Three lines attach independently, each only when it applies:

- `Closes #123` / `Fixes #123`, when there's an issue
- a short code block, when a call site or API shape is the clearest way to show the change
- one line on how it was verified, when verification was non-obvious -- new test file names don't need saying, they're in the diff

Draft the one-sentence version first, as actual text on the page. Keep it. When you show the draft, put it above the body you propose, labeled, with one line on what the rest of the body says that it doesn't. Judging your own draft in the abstract is nearly free and always comes back justified. Displaying the version you threw away next to your reason for throwing it away is what makes the choice real, and it hands the user the shorter option to accept in one word.

A body that is nothing but `Closes #412` is a finished body. There is no length you are expected to reach.

That's the whole body. No section headings. No file-by-file walkthrough. No bulleted list restating each commit; the commit log exists and is one click away. No "this PR..." preamble -- start with the substance.

## Examples

A body that is only a link, where the title already carries the change:

> Closes #488

One sentence:

> `spread_to_price` now raises for callable bonds whose next-call date is in the past. It used to return NaN and poison downstream aggregates.

Two paragraphs on one change, where the second is a caveat named as one:

> Curve bootstrapping is now memoized on settlement date for the life of a `price_batch` call. Every bond in a batch re-ran it before, and that dominated runtime on the 40k-bond nightly job.
>
> The cache is per call, not per process. Settlement-date curves change intraday, and a process-wide cache would serve stale ones.
>
> Closes #412

Padded, then the same PR in order:

> The `retry_policy` argument was being dropped because `_build_config` shallow-copies the options dict at line 88 before the decorator merges defaults, so any key set by the caller after import time was silently discarded. This affected `retry_policy`, `timeout_s`, and `backoff_factor`. Changed the shallow copy to a deep merge, which is behavior-preserving for every other key -- a targeted fix to just `retry_policy` was possible but would leave the same bug latent for the other two, so the broader fix was taken.

> `_build_config` now deep-merges caller options into the defaults. It shallow-copied before, so any option set after import was dropped.

Rationale first, then the same PR with the fact first:

> `effects.py` is otherwise a pure data vocabulary -- fifty-odd effect types and no registries -- and the attack-strength registry plus `effective_strength` were the only thing in it walking the board. Both moved to `units.py`, next to `attackable`, which is the other half of the same attack-targeting rules. `AttackEffect.perform` reads `effective_strength`, so it takes a deferred import: `AttackEffect` and its three subclasses can't move along with it, because the card-vocabulary page guard filters on `__module__` and relocating them would drop four types off that page with nothing failing.

> Moved the attack-strength registry and `effective_strength` from `effects.py` to `units.py`, next to `attackable`. `effects.py` now holds only effect types, and the attack-targeting rules live in one module.
>
> `AttackEffect` and its subclasses stay in `effects.py` and import `effective_strength` lazily. The card-vocabulary page guard filters on `__module__`, so moving them would silently drop four types from that page.
>
> Adds a test for `effective_strength` when the target has already left the table, which had no coverage.

Every fact from the first version is in the second. The difference is that each sentence has an antecedent on the page.

## Read the draft against these

Named failure modes. Check the draft against each one by name before showing it.

- Ticket paraphrase. The body restates the linked issue in different words. The issue is one click away and adds nothing here.
- The story of the work. How you found the cause, what you tried first, what you decided against and why. It belongs in chat, or in a follow-up issue if something is genuinely left undone. A mechanism is not story when it explains a change already stated on the page. It is story when it stands in for that statement.
- Enumeration the prose doesn't need. Exact versions, enumerated renames, file counts. Let the diff supply the list. This licenses cutting lists, never replacing an identifier with a description you invented.
- Unfalsifiable adjectives. "Cleaner", "more robust", "improved performance", with nothing a reviewer can check. Measure it or cut it.
- Verification theater. "Tested thoroughly." Name what was checked and why it was non-obvious, or say nothing.
- A justification with no antecedent. A sentence that explains why, when the what has not appeared yet. Move the what in front of it.
- A coined phrase where an identifier belongs. "The attack-targeting rules", "the card vocabulary", "the escape guard", when the code has a name. Use the name, then say what kind of thing it is.

The trivial PR is where padding is worst. With nothing much to say, the pull is to manufacture something -- restating the title, narrating the process, inflating a one-line fix into a paragraph. A one-line body on a one-line change is the correct output, not a failure to try harder.

## Voice

Write for a reviewer who has never opened this repo and is reading in a hurry. Contractions are fine. Plain declarative sentences are the goal. No sentence fragments.

American English, always. British spellings in a PR body are an instant tell.

Name code by its identifier, then say in plain words what kind of thing it is. Never substitute a description you coined for a name that exists.

No figurative verbs for what code does. Code does not walk, reach across, ride on, park, sit empty, or fold. It calls, reads, imports, registers, moves, returns.

Skip the technical-report register. If a phrase would sound stilted said out loud, it's wrong here. No hedging a decision you already made, no defending one nobody questioned, no announcing what the change does before doing it ("this PR introduces...").

Plain register is not permission to be cute. Never soften a real technical consequence with diminishing or jokey framing -- "one wrinkle", "small gotcha", "fun catch", "worth noting though". And never signpost a hazard instead of stating it -- "worth a close look", "the interesting bit", "keep an eye on", "one thing to watch", "heads up". That phrasing promises significance and makes the reviewer go find it; name the hazard directly, so they read the consequence before they read the diff. A caveat that changes behavior, breaks an invariant, or needs the reviewer's decision is stated flatly as what it is. If it's important enough to include, it's important enough to say straight.

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
