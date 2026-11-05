# Posting the review

Read this in Phase 7, after the draft is authorized.

`<skill>` below is `/Users/jesse.grabowski/.claude/skills/lazy-review`. Spell it
out in full, invoke the script with `python`, and run each command as its own
Bash call. The permission allow rule matches only that exact prefix. A `cd`, a
`~`, a `&&` chain, a loop, or a `$(...)` substitution falls through to the auto
mode classifier, which blocks GitHub writes. The same applies to every `gh`
read during the review: one `gh pr view` / `gh pr diff` / `gh pr list` per call,
and `gh api` reads only with `--method GET`, never inside a loop.

## Validate the anchors first

GitHub only accepts an inline comment on a line inside a diff hunk, and it
rejects the whole review if any single anchor is invalid.

```bash
python <skill>/scripts/review_payload.py validate \
  --payload <vault>/03_review_payload.md --repo <owner/name> --pr <n>
```

Fix every reported miss before going further. When an anchor lands outside a
hunk, the usual cause is that you cited a definition by memory -- grep for the
symbol and use its real line.

## Post

```bash
python <skill>/scripts/review_payload.py post \
  --payload <vault>/03_review_payload.md --repo <owner/name> --pr <n>
```

The event is the payload's `Event:` line, and the body is its blockquote, which
may be empty when the event is `APPROVE`. When the user changes either at post
time, edit the payload and post it. Never fall back to a raw `gh api` call to
get an empty body or a different event, because the note then stops matching
what was posted.

Only rows under `## Inline comments` are posted. The script names any `C` row it
found elsewhere in the note, so a held comment the user cleared has to be moved
into that section first.

Three things the script handles that are easy to get wrong by hand.

**Large reviews go up in chunks.** More than 30 comments in one request trips
GitHub's secondary rate limit. Above that size the script opens a pending review
with the first 30, attaches the rest one at a time, and submits at the end. If it
stops partway, the pending review stays on the PR, invisible to the author, and
running `post` again resumes it without duplicating a comment. Wait out a rate
limit before rerunning. Never split a payload by hand into several reviews.

**A 502 does not mean the review failed.** This endpoint returns server errors
after successfully creating the review. Never retry blind -- a retry double-posts
every comment. The script checks for an existing review before it posts and again
after a failure, and you should check too if you ever post manually.

**Post before any retargeting.** If your review asks the author to change the
base branch, post first. Comments already posted survive a retarget, but the
payload does not: re-validating afterwards reports every anchor in the inherited
files as outside the diff, because those files are no longer in it. Once the base
moves, that payload can only be posted against the new scope.

Report the review URL and what the author now owns.
