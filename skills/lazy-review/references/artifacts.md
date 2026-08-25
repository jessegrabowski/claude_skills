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
01_inventory.md       Phase 2 + 3 -- what was added, mechanical results, agent findings
02_findings.md        Phase 4 + 5 -- consolidated findings, severity, confidence
03_review_payload.md  Phase 6 -- the review body and the anchor table
```

Never leave these in the repo, in `/tmp`, or in a scratchpad. The user will not
find them there.

`03_review_payload.md` is the file `review_payload.py` reads, so its shape is
fixed: the review body in a blockquote under `## Review body`, then a table of
inline comments whose rows look like

```
| C01 | `path/to/file.py` | 581 | what to do ... |
```

The path is repo-relative, exactly as GitHub spells it in the diff --
`src/pkg/pkg/data_utils.py`, never the bare `data_utils.py`. Findings notes tend
to shorten paths once a file is under discussion, and copying that shortened form
into the payload makes every anchor on that file invalid. Take the path from the
diff, not from the prose around the finding.

What you validate is what you post, so edit the payload rather than the API call.
