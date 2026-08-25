# Posting the review

Read this in Phase 7, after the draft is authorized.

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
  --payload <vault>/03_review_payload.md --repo <owner/name> --pr <n> \
  --event REQUEST_CHANGES
```

Two things the script handles that are easy to get wrong by hand.

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
