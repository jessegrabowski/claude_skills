#!/usr/bin/env python3
"""Validate and post a lazy-review payload.

The payload is the markdown note written in Phase 6: an `Event:` line, a review
body in a blockquote under `## Review body` (empty is allowed with APPROVE), and,
under `## Inline comments`, a table whose rows look like

    | C01 | `path/to/file.py` | 581 | what to do ... |

Only rows inside the `## Inline comments` section are posted. Held, dropped and
clearance tables elsewhere in the note are never read.

Two subcommands:

    validate   check every anchor against the PR's own diff, print misses
    post       build the API payload and submit it

Both read the same payload file, so what you validate is what you post. The
event comes from the payload too, so the note records what was actually posted.

A review with more than CHUNK_SIZE comments is posted as one pending review that
receives its comments a few at a time and is submitted at the end. A run that
stops partway leaves that pending review on the PR, and running `post` again
resumes it, skipping the comments already attached.
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
import time

ROW = re.compile(r"^\|\s*(C\d+)\s*\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|\s*(.*?)\s*\|\s*$")
EVENT = re.compile(r"^Event:\s*(\w+)\s*$", re.MULTILINE)
EVENTS = ("REQUEST_CHANGES", "COMMENT", "APPROVE")
BODY_LIMIT = 65536
CHUNK_SIZE = 30
SECONDS_BETWEEN_COMMENTS = 2.0
ADD_THREAD = """
mutation($review: ID!, $path: String!, $line: Int!, $body: String!) {
  addPullRequestReviewThread(input: {pullRequestReviewId: $review, path: $path,
                                     line: $line, side: RIGHT, body: $body}) {
    thread { id }
  }
}
"""


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


def section(src: str, heading: str) -> str | None:
    """Text under `## <heading>` up to the next `## ` heading, or None if absent."""
    match = re.search(rf"^## {re.escape(heading)}\s*$", src, re.MULTILINE)
    if not match:
        return None
    rest = src[match.end() :]
    following = re.search(r"^## ", rest, re.MULTILINE)
    return rest[: following.start()] if following else rest


def parse_payload(path: str) -> tuple[str, str, list[dict]]:
    """Return (event, review_body, comments) from the payload note."""
    src = open(path).read()

    event_match = EVENT.search(src)
    if not event_match or event_match.group(1) not in EVENTS:
        raise SystemExit(f"{path}: needs an 'Event: <{'|'.join(EVENTS)}>' line")
    event = event_match.group(1)

    body_section = section(src, "Review body")
    if body_section is None:
        raise SystemExit(f"{path}: no '## Review body' section found")
    body_lines = []
    for line in body_section.split("\n---", 1)[0].splitlines():
        if line.startswith("> "):
            body_lines.append(line[2:])
        elif line.strip() == ">":
            body_lines.append("")
    body = "\n".join(body_lines).strip()
    if not body and event != "APPROVE":
        raise SystemExit(f"{path}: an empty review body is only accepted with APPROVE")

    comments = []
    seen = set()
    for line in (section(src, "Inline comments") or "").splitlines():
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
    stray = [
        m.group(1)
        for line in src.splitlines()
        if (m := ROW.match(line)) and m.group(1) not in seen
    ]
    if stray:
        print(
            f"not posted, outside '## Inline comments': {', '.join(stray)}",
            file=sys.stderr,
        )
    return event, body, comments


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


def reviews_by(repo: str, pr: int, login: str) -> list[dict]:
    """Every review by `login` on the PR, oldest first, pending ones included."""
    reviews = json.loads(gh("api", f"/repos/{repo}/pulls/{pr}/reviews", "--paginate"))
    return [r for r in reviews if r.get("user", {}).get("login") == login]


def gh_post_json(endpoint: str, payload: dict) -> subprocess.CompletedProcess:
    """POST a JSON payload to a REST endpoint without raising on failure."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump(payload, fh, indent=1)
    return subprocess.run(
        ["gh", "api", "--method", "POST", endpoint, "--input", fh.name],
        capture_output=True,
        text=True,
    )


def api_comment(comment: dict) -> dict:
    return {key: value for key, value in comment.items() if key != "cid"}


def post_single(
    args,
    event: str,
    body: str,
    comments: list[dict],
    sha: str,
    login: str,
    prior: list[dict],
) -> int:
    print(
        f"posting {len(comments)} comments as {event} "
        f"on {args.repo}#{args.pr} @ {sha[:8]}"
    )
    payload = {
        "commit_id": sha,
        "event": event,
        "body": body,
        "comments": [api_comment(c) for c in comments],
    }
    p = gh_post_json(f"/repos/{args.repo}/pulls/{args.pr}/reviews", payload)
    if p.returncode == 0:
        print(json.loads(p.stdout)["html_url"])
        return 0

    # This endpoint returns 5xx *after* creating the review. Retrying double-posts
    # every comment, so confirm what actually landed before doing anything else.
    print(f"request failed:\n{p.stderr.strip()}", file=sys.stderr)
    print("\nchecking whether it landed anyway...", file=sys.stderr)
    known = {r["id"] for r in prior}
    landed = [r for r in reviews_by(args.repo, args.pr, login) if r["id"] not in known]
    if landed:
        print(f"it did: review {landed[-1]['id']} ({landed[-1]['state']}).")
        print(landed[-1]["html_url"])
        print("Do NOT retry.")
        return 0
    print("no review found -- safe to retry.", file=sys.stderr)
    return 1


def post_chunked(
    args, event: str, body: str, comments: list[dict], sha: str, pending: dict | None
) -> int:
    base = f"/repos/{args.repo}/pulls/{args.pr}/reviews"
    if pending is None:
        first, rest = comments[:CHUNK_SIZE], comments[CHUNK_SIZE:]
        print(
            f"opening a pending review with {len(first)} of {len(comments)} comments "
            f"on {args.repo}#{args.pr} @ {sha[:8]}"
        )
        p = gh_post_json(
            base, {"commit_id": sha, "comments": [api_comment(c) for c in first]}
        )
        if p.returncode:
            raise SystemExit(
                f"opening the pending review failed:\n{p.stderr.strip()}\n"
                "Run post again: it resumes any pending review that landed."
            )
        pending = json.loads(p.stdout)
    else:
        attached = json.loads(
            gh("api", f"{base}/{pending['id']}/comments", "--paginate")
        )
        done = {
            (c["path"], c.get("line") or c.get("original_line"), c["body"])
            for c in attached
        }
        rest = [c for c in comments if (c["path"], c["line"], c["body"]) not in done]
        print(
            f"resuming pending review {pending['id']}: "
            f"{len(comments) - len(rest)} attached, {len(rest)} to go"
        )

    for position, comment in enumerate(rest, start=1):
        time.sleep(SECONDS_BETWEEN_COMMENTS)
        p = subprocess.run(
            [
                "gh",
                "api",
                "graphql",
                "-f",
                f"query={ADD_THREAD}",
                "-f",
                f"review={pending['node_id']}",
                "-f",
                f"path={comment['path']}",
                "-F",
                f"line={comment['line']}",
                "-f",
                f"body={comment['body']}",
            ],
            capture_output=True,
            text=True,
        )
        if p.returncode or '"errors"' in p.stdout:
            print(
                f"stopped at {comment['cid']} ({position - 1} of {len(rest)} added):\n"
                f"{(p.stderr or p.stdout).strip()}",
                file=sys.stderr,
            )
            print(
                f"Pending review {pending['id']} keeps what was attached. Wait out any "
                "rate limit, then run post again to resume.",
                file=sys.stderr,
            )
            return 1

    p = gh_post_json(f"{base}/{pending['id']}/events", {"event": event, "body": body})
    if p.returncode:
        raise SystemExit(
            f"submitting pending review {pending['id']} failed:\n"
            f"{p.stderr.strip()}\nRun post again to retry the submit."
        )
    print(json.loads(p.stdout)["html_url"])
    return 0


def cmd_validate(args) -> int:
    event, body, comments = parse_payload(args.payload)
    problems = check(comments, commentable_lines(args.repo, args.pr))
    print(f"event:       {event}")
    print(f"review body: {len(body)} chars")
    print(f"comments:    {len(comments)}")
    if len(comments) > CHUNK_SIZE:
        print(
            f"             more than {CHUNK_SIZE}, so post will attach them in chunks"
        )
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems:
            print(f"  {p}")
        print("\nFix these before posting; one bad anchor rejects the whole review.")
        return 1
    print("\nall anchors inside a diff hunk, no leftover markup -- ready to post")
    return 0


def cmd_post(args) -> int:
    event, body, comments = parse_payload(args.payload)
    problems = check(comments, commentable_lines(args.repo, args.pr))
    if problems:
        print("refusing to post, validate first:")
        for p in problems:
            print(f"  {p}")
        return 1

    login = gh("api", "user", "-q", ".login").strip()
    pr_view = json.loads(
        gh(
            "pr",
            "view",
            str(args.pr),
            "--repo",
            args.repo,
            "--json",
            "author,headRefOid",
        )
    )
    if login == pr_view["author"]["login"] and event != "COMMENT":
        raise SystemExit(f"{login} authored this PR; GitHub rejects a self {event}")

    prior = reviews_by(args.repo, args.pr, login)
    pending = next((r for r in prior if r["state"] == "PENDING"), None)
    submitted = [r for r in prior if r["state"] != "PENDING"]
    if pending is None and submitted and not args.allow_duplicate:
        raise SystemExit(
            f"{login} already has review {submitted[-1]['id']} "
            f"({submitted[-1]['state']}) "
            f"on #{args.pr}. Pass --allow-duplicate only if a second review is "
            "genuinely intended."
        )

    sha = pr_view["headRefOid"]
    if pending is not None or len(comments) > CHUNK_SIZE:
        return post_chunked(args, event, body, comments, sha, pending)
    return post_single(args, event, body, comments, sha, login, prior)


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
                "--allow-duplicate",
                action="store_true",
                help="post even though this user already reviewed the PR",
            )
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
