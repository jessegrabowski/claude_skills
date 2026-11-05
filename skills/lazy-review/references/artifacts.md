# Review artifacts

Write these as you go, one numbered note per phase, into

```
<review-root>/<repo>/PR_Review_<num>_<YYYY-MM-DD>/
```

`<review-root>` is machine-local. Take it from `CLAUDE.local.md`; if it isn't set
there, ask once and use the answer for the rest of the session. Use the
`currentDate` from the runtime for the folder name.

```
00_scope.md           Phase 0 -- real diff, base-branch finding, size, commit hygiene
00_rules.md           Phase 1 -- numbered convention checklist, each rule with its source
01_inventory.md       Phase 2 + 3 -- what was added, mechanical results, agent findings,
                      convention_check.py leads kept or dropped
02_findings.md        Phase 4 + 5 -- consolidated findings, severity, confidence, and the
                      rule coverage table
03_review_payload.md  Phase 6 -- the event, the review body and the anchor table
04_pass_<name>.md     Phase 4 -- one report per pass, opening with how it was invoked, the
                      files covered, and confirmation that 00_rules.md was applied
```

Never leave these in the repo, in `/tmp`, or in a scratchpad. The user will not
find them there.

## Archiving older reviews

Before writing the new folder, move the repo's finished reviews out of the way.
Every folder already in `<review-root>/<repo>/` belongs to a PR: the number in
`PR_Review_<num>_...` or `Fresh_Review_<num>_...`, or, for
`Fresh_Review_<branch>_...`, the PR opened from the branch its `00_brief.md`
names. Look each one up with a single command, `gh pr view <num> --repo
<owner/name> --json state` or `gh pr list --repo <owner/name> --head <branch>
--state all --json number,state`. Move every folder whose PR is `MERGED` or
`CLOSED` to `<review-archive>/<repo>/`, and never overwrite a folder already
there. Leave a folder in place when its PR is open or when no PR exists.

`<review-archive>` is machine-local, set next to `<review-root>` in
`CLAUDE.local.md`. If it isn't set, skip this step and say so. Wikilinks into a
moved folder keep resolving, because Obsidian matches `Reviews/<repo>/...`
against the end of the full path. Report what moved in one line.

`03_review_payload.md` is the file `review_payload.py` reads, so its shape is
fixed:

```
Event: APPROVE

## Review body

> one line, or nothing

---

## Inline comments

| id | path | line | comment |
|---|---|---|---|
| C01 | `path/to/file.py` | 581 | what to do ... |

## Held for clearance

| H01 | `path/to/file.py` | 90 | taste comment awaiting the user ... |
```

Only rows under `## Inline comments` are posted. Held comments take `H` ids and
live in their own section. When the user clears one, move it into the
inline-comments table with the next `C` id. Ids run without gaps, and every
finding in `02_findings.md` ends with a disposition: the `C` or `H` id it became,
or `dropped` with a reason. A finding that disappears between the findings note
and the payload with no disposition is a bookkeeping failure, and a blocker
dropped that way leaves the event arguing for a change nobody asked for.

The path is repo-relative, exactly as GitHub spells it in the diff --
`src/pkg/pkg/data_utils.py`, never the bare `data_utils.py`. Findings notes tend
to shorten paths once a file is under discussion, and copying that shortened form
into the payload makes every anchor on that file invalid. Take the path from the
diff, not from the prose around the finding.

What you validate is what you post, so edit the payload rather than the API call.
