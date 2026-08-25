#!/usr/bin/env python3
"""Validate and post a lazy-review payload.

The payload is the markdown note written in Phase 6: a review body in a
blockquote under `## Review body`, and a table of inline comments whose rows look
like

    | C01 | `path/to/file.py` | 581 | what to do ... |

Two subcommands:

    validate   check every anchor against the PR's own diff, print misses
    post       build the API payload and submit it

Both read the same payload file, so what you validate is what you post.
"""

import argparse
import json
import re
import subprocess
import sys

ROW = re.compile(r"^\|\s*(C\d+)\s*\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|\s*(.*?)\s*\|\s*$")
BODY_LIMIT = 65536


def gh(*args: str) -> str:
    """Run a gh command and return stdout, raising with stderr on failure."""
    p = subprocess.run(["gh", *args], capture_output=True, text=True)
    if p.returncode:
        raise SystemExit(f"gh {' '.join(args)} failed:\n{p.stderr.strip()}")
    return p.stdout


def commentable_lines(repo: str, pr: int) -> dict[str, set[int]]:
    """RIGHT-side line numbers inside a diff hunk, per file, from the PR's own diff.

    Uses the PR diff rather than a local `git diff` so the result matches what
    GitHub will accept even when local refs are stale.
    """
    diff = gh("pr", "diff", str(pr), "--repo", repo)
    out: dict[str, set[int]] = {}
    path = None
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            path = line[6:]
            out.setdefault(path, set())
        elif line.startswith("@@") and path:
            m = re.search(r"\+(\d+)(?:,(\d+))?", line)
            if m:
                start = int(m.group(1))
                count = int(m.group(2) or 1)
                out[path].update(range(start, start + count))
    return out


def parse_payload(path: str) -> tuple[str, list[dict]]:
    """Return (review_body, comments) from the payload note."""
    src = open(path).read()

    if "## Review body" not in src:
        raise SystemExit(f"{path}: no '## Review body' section found")
    section = src.split("## Review body", 1)[1].split("\n---", 1)[0]
    body_lines = []
    for line in section.splitlines():
        if line.startswith("> "):
            body_lines.append(line[2:])
        elif line.strip() == ">":
            body_lines.append("")
    body = "\n".join(body_lines).strip()
    if not body:
        raise SystemExit(f"{path}: review body blockquote is empty")

    comments = []
    seen = set()
    for line in src.splitlines():
        m = ROW.match(line)
        if not m:
            continue
        cid, file_path, lineno, text = m.groups()
        if cid in seen:
            raise SystemExit(f"{path}: duplicate comment id {cid}")
        seen.add(cid)
        text = text.replace("<br>", "\n").replace(r"\|", "|").strip()
        comments.append(
            {
                "cid": cid,
                "path": file_path,
                "line": int(lineno),
                "side": "RIGHT",
                "body": text,
            }
        )
    if not comments:
        raise SystemExit(
            f"{path}: no comment rows matched; expected '| C01 | `path` | 12 | ... |'"
        )
    return body, comments


def check(comments: list[dict], allowed: dict[str, set[int]]) -> list[str]:
    """Return a human-readable problem per bad anchor; empty list means good."""
    problems = []
    for c in comments:
        lines = allowed.get(c["path"])
        if lines is None:
            problems.append(f"{c['cid']}  {c['path']}  -- file not in the PR diff")
        elif c["line"] not in lines:
            near = sorted(x for x in lines if abs(x - c["line"]) <= 25)[:6]
            hint = f"nearest in-hunk: {near}" if near else "no hunk within 25 lines"
            problems.append(
                f"{c['cid']}  {c['path']}:{c['line']}  -- outside a hunk, {hint}"
            )
        if "<br>" in c["body"] or r"\|" in c["body"]:
            problems.append(f"{c['cid']}  -- unconverted table markup left in body")
        if len(c["body"]) > BODY_LIMIT:
            problems.append(
                f"{c['cid']}  -- body is {len(c['body'])} chars, limit {BODY_LIMIT}"
            )
    return problems


def existing_review(repo: str, pr: int, login: str) -> dict | None:
    """The most recent non-comment review by `login`, if any."""
    reviews = json.loads(gh("api", f"/repos/{repo}/pulls/{pr}/reviews", "--paginate"))
    mine = [r for r in reviews if r.get("user", {}).get("login") == login]
    return mine[-1] if mine else None


def cmd_validate(args) -> int:
    body, comments = parse_payload(args.payload)
    problems = check(comments, commentable_lines(args.repo, args.pr))
    print(f"review body: {len(body)} chars")
    print(f"comments:    {len(comments)}")
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems:
            print(f"  {p}")
        print("\nFix these before posting; one bad anchor rejects the whole review.")
        return 1
    print("\nall anchors inside a diff hunk, no leftover markup -- ready to post")
    return 0


def cmd_post(args) -> int:
    body, comments = parse_payload(args.payload)
    problems = check(comments, commentable_lines(args.repo, args.pr))
    if problems:
        print("refusing to post, validate first:")
        for p in problems:
            print(f"  {p}")
        return 1

    login = gh("api", "user", "-q", ".login").strip()
    author = gh(
        "pr",
        "view",
        str(args.pr),
        "--repo",
        args.repo,
        "--json",
        "author",
        "-q",
        ".author.login",
    ).strip()
    if login == author and args.event == "REQUEST_CHANGES":
        raise SystemExit(
            f"{login} authored this PR; GitHub rejects a self REQUEST_CHANGES"
        )

    prior = existing_review(args.repo, args.pr, login)
    if prior and not args.allow_duplicate:
        raise SystemExit(
            f"{login} already has review {prior['id']} ({prior['state']}) on #{args.pr}. "
            "Pass --allow-duplicate only if a second review is genuinely intended."
        )

    sha = gh(
        "pr",
        "view",
        str(args.pr),
        "--repo",
        args.repo,
        "--json",
        "headRefOid",
        "-q",
        ".headRefOid",
    ).strip()
    payload = {
        "commit_id": sha,
        "event": args.event,
        "body": body,
        "comments": [{k: v for k, v in c.items() if k != "cid"} for c in comments],
    }
    with open("/tmp/lazy_review_payload.json", "w") as fh:
        json.dump(payload, fh, indent=1)

    print(
        f"posting {len(comments)} comments as {args.event} on {args.repo}#{args.pr} @ {sha[:8]}"
    )
    p = subprocess.run(
        [
            "gh",
            "api",
            "--method",
            "POST",
            f"/repos/{args.repo}/pulls/{args.pr}/reviews",
            "--input",
            "/tmp/lazy_review_payload.json",
        ],
        capture_output=True,
        text=True,
    )
    if p.returncode == 0:
        print(json.loads(p.stdout)["html_url"])
        return 0

    # This endpoint returns 5xx *after* creating the review. Retrying double-posts
    # every comment, so confirm what actually landed before doing anything else.
    print(f"request failed:\n{p.stderr.strip()}", file=sys.stderr)
    print("\nchecking whether it landed anyway...", file=sys.stderr)
    landed = existing_review(args.repo, args.pr, login)
    if landed and (not prior or landed["id"] != prior["id"]):
        n = len(
            json.loads(
                gh("api", f"/repos/{args.repo}/pulls/{args.pr}/comments", "--paginate")
            )
        )
        print(
            f"it did: review {landed['id']} ({landed['state']}), {n} comments on the PR."
        )
        print(landed["html_url"])
        print("Do NOT retry.")
        return 0
    print("no review found -- safe to retry.", file=sys.stderr)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("validate", cmd_validate), ("post", cmd_post)):
        p = sub.add_parser(name)
        p.add_argument("--payload", required=True, help="path to 03_review_payload.md")
        p.add_argument("--repo", required=True, help="owner/name")
        p.add_argument("--pr", required=True, type=int)
        p.set_defaults(fn=fn)
        if name == "post":
            p.add_argument(
                "--event",
                default="REQUEST_CHANGES",
                choices=["REQUEST_CHANGES", "COMMENT", "APPROVE"],
            )
            p.add_argument(
                "--allow-duplicate",
                action="store_true",
                help="post even though this user already reviewed the PR",
            )
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
