---
name: fresh-review
description: Hands the current change to a fresh subagent that runs /code-review (deep by default) knowing only the problem, the design principles, and the scope -- never the plan or the design history -- then saves the brief, the verbatim review, and a triage note to the Obsidian vault. Use when the user wants an independent, adversarial review of work built up in this conversation.
disable-model-invocation: true
argument-hint: "[scope: PR number, branch, base..head, or paths] [--quick|--standard|--deep]"
---

# fresh-review

A review written by the agent that built the code inherits every assumption that shaped it. The point of this skill is a reviewer that has none of them: it knows what the code is for and what good looks like, and it has to reach its own conclusions about whether the code gets there. Everything below exists to keep that reviewer's context clean and to keep its findings from being filtered on the way back.

## Input

$ARGUMENTS

Scope defaults to the pending change on the current branch: the diff against the merge-base with the default branch, plus untracked files that belong to the change. Depth defaults to `--deep`. If the arguments name neither and the branch has no diff, ask.

## 1. Resolve the scope

Turn the scope into something the reviewer can act on without this conversation: a PR number and repo, a `base...head` range, or an explicit list of paths. List the changed files (`git diff --stat` against the base) so the brief names them. When the change touches files that are not in scope -- vendored code, generated files, an unrelated fix riding along -- say which ones to skip.

## 2. Write the brief

The brief has exactly three parts.

**Problem.** Two to five sentences on what the change is for: the behavior or capability that is missing or broken without it, and who or what depends on it. Describe the goal, never the solution. "Bond prices from the surrogate drift from the full model above 30y maturity" is a problem. "We added a maturity-bucketed correction" is a solution and stays out.

**Principles.** What the code is held to. Start from the defaults: maintainability, readability, extensibility, simplicity over cleverness, and tests that pin behavior. Then add the repo's own. Read the project `CLAUDE.md` (and any `CLAUDE.md` in the directories the change touches), pull the rules that bear on review -- architecture boundaries, naming, error handling, testing conventions, performance constraints -- and quote them with their file path. Point the reviewer at `~/.claude/CLAUDE.md` for the user's general code style. Include a principle stated in this conversation only if it would hold for any change to this repo. A principle invented to justify this particular change is a decision in disguise.

**Scope.** The target from step 1, the file list, and what to skip.

**What never goes in the brief:** the plan, the alternatives tried or rejected, the reasons behind design choices, earlier review rounds, known weaknesses the user has accepted, or any claim that the code is correct, tested, or finished. Each of these tells the reviewer what to conclude, and a reviewer told why a choice was made will check the reasoning instead of the code. If a reviewer raises something already decided, that is information. The triage step handles it.

If you cannot state the problem or the repo-specific principles from the conversation and the repo, ask the user before going further. Otherwise print the brief in chat and continue without waiting. It is saved in the vault, so it can be checked afterwards.

## 3. Launch the reviewer

Spawn one `general-purpose` agent. **Never use a `fork`.** A fork inherits this whole conversation, plan included, which defeats the purpose of the skill. Do not pass a `model` override.

The prompt is the brief followed by these instructions, verbatim apart from the placeholders:

```
Run the code-review skill on this scope by calling the Skill tool:
  Skill(skill="code-review", args="<depth> <scope>")
Do not write a review of your own instead, and do not summarize or reformat the skill's output. If the Skill tool is unavailable or the skill fails to load, stop and report that as your entire answer.

This review is read-only. Do not edit files, run git commands that write, or comment on any PR.

Your final message must contain exactly two things, in order:
1. The line "code-review invoked: <the args you passed>".
2. The complete code-review output, unchanged.
```

When the agent finishes, check the first line. If it is missing, or the output lacks code-review's section structure (Verdict, Severity, Blockers, ...), the reviewer improvised. Report that to the user and do not save the output as a review.

## 4. Relay and triage

Give the user the review first, unfiltered: verdict, severity, and every blocker and finding as the reviewer wrote them. Then add a triage section of your own, clearly labeled, that uses the context the reviewer lacked. For each finding say one of:

- **new** -- not considered before; worth acting on.
- **already decided** -- re-raises a choice made in this conversation. Name the decision and the reason it was made, and say whether the finding changes the case for it.
- **wrong** -- the reviewer misread the code. Cite the `file:line` that shows it.

Never drop a finding because it conflicts with the plan. A finding marked already decided stays in the review, and the user decides whether the decision holds.

## 5. Save to the vault

Write the review folder to

```
<review-root>/<repo>/Fresh_Review_<pr-or-branch>_<YYYY-MM-DD>/
```

`<review-root>` is the same machine-local root `lazy-review` uses. Take it from `CLAUDE.local.md`; if it isn't set there, ask once. `<pr-or-branch>` is the PR number when there is one, otherwise the branch name with `/` replaced by `-`. Use the runtime's current date. If the folder exists, append `_2`, `_3`, and so on. Never overwrite an earlier review.

```
00_brief.md    the exact brief sent to the reviewer, plus repo, base, head SHA, depth
01_review.md   the reviewer's output, verbatim
02_triage.md   the triage from step 4
```

Write each paragraph as a single line, because Obsidian soft-wraps notes to the pane width. If the work follows a `plan-scaffold` plan in the vault, link it from `00_brief.md` and `02_triage.md` with a wikilink, and add a link to the review folder under the matching step's PR in the plan. The link lives only in the vault notes. It never goes into the brief.

## Hand back

Say where the folder landed, give the verdict and severity in one line, and list the findings triaged as new.
