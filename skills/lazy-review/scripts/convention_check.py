#!/usr/bin/env python3
"""Flag convention leads on the lines a PR adds, read from git refs without a checkout.

Every hit is a lead for Phase 3, not a finding. Verify each one against the rules
file before it reaches 02_findings.md.

    python convention_check.py --repo <path> --base origin/main --head origin/<branch>
"""

import argparse
import ast
import io
import re
import subprocess
import tokenize
from pathlib import PurePosixPath

DOCSTRING_SECTION = re.compile(r"^\s*(Parameters|Returns|Yields|Raises|Warns)\s*\n\s*-{3,}", re.M)
HISTORY_WORDS = re.compile(
    r"\b(legacy|previous(ly)?|used to|no longer|formerly|mirrors|replaces|the old|instead of)\b",
    re.I,
)
SECTION_DIVIDER = re.compile(r"^#\s*([-=#*~_])\1{3,}")
DEFINITION = re.compile(r"^\s*(?:async\s+)?(?:def|class)\s+(\w+)")
CONTAINER_METHODS = {
    "append", "endswith", "extend", "format", "get", "insert", "items", "join", "keys", "pop",
    "replace", "setdefault", "split", "startswith", "update", "values",
}


def git(repo: str, *args: str) -> str:
    """Return stdout of a git command run in `repo`."""
    return subprocess.run(["git", "-C", repo, *args],
                          capture_output=True,
                          text=True,
                          check=True).stdout


def git_or_none(repo: str, *args: str) -> str | None:
    """Stdout of a git command, or None when it fails (a path absent from a ref)."""
    result = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else None


def added_lines(repo: str, base: str, head: str) -> dict[str, set[int]]:
    """Map each changed path to the head-side line numbers the diff adds."""
    diff = git(repo, "diff", "-U0", f"{base}...{head}")
    out: dict[str, set[int]] = {}
    path = None
    for line in diff.splitlines():
        if line.startswith("+++ "):
            path = None if line.endswith("/dev/null") else line[6:]
            if path:
                out.setdefault(path, set())
        elif line.startswith("@@") and path:
            match = re.search(r"\+(\d+)(?:,(\d+))?", line)
            start = int(match.group(1))
            count = int(match.group(2) or 1)
            out[path].update(range(start, start + count))
    return out


def project_callables(repo: str, head: str) -> set[str]:
    """Names of every function and class defined in the head tree's Python files."""
    listing = git(repo, "grep", "-h", "-E", r"^[[:space:]]*(async[[:space:]]+)?(def|class) [A-Za-z_]", head, "--", "*.py")
    defined = {match.group(1) for line in listing.splitlines() if (match := DEFINITION.match(line))}
    return defined - CONTAINER_METHODS


def returns_value(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """True when the function annotates or returns a value other than None."""
    if node.returns is not None:
        return not (isinstance(node.returns, ast.Constant) and node.returns.value is None)
    return any(isinstance(child, ast.Return) and child.value is not None
               for child in ast.walk(node))


def callee_name(call: ast.Call) -> str | None:
    """The bare name a call resolves to, for `f(...)` and `obj.f(...)`."""
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def parameter_defaults(node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, ast.expr | None]:
    """Each parameter's default expression, None when it has no default."""
    arguments = node.args
    positional = arguments.posonlyargs + arguments.args
    padded = [None] * (len(positional) - len(arguments.defaults)) + list(arguments.defaults)
    defaults = {arg.arg: default for arg, default in zip(positional, padded)}
    defaults.update({arg.arg: default for arg, default in zip(arguments.kwonlyargs, arguments.kw_defaults)})
    return defaults


def is_option_default(default: ast.expr | None) -> bool:
    """True for a bool or string literal default, the shape of a mode switch."""
    return isinstance(default, ast.Constant) and isinstance(default.value, (bool, str))


def class_field_defaults(node: ast.ClassDef) -> dict[str, tuple[int, ast.expr | None]]:
    """Each annotated class-body field's line and default, as dataclasses declare them."""
    return {statement.target.id: (statement.lineno, statement.value)
            for statement in node.body
            if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name)}


def option_leads(base_source: str | None, head_tree: ast.Module) -> list[tuple[int, str, str]]:
    """New bool or string-mode parameters and fields on functions and classes that existed at the base."""
    if base_source is None:
        return []
    try:
        base_tree = ast.parse(base_source)
    except SyntaxError:
        return []
    function_types = (ast.FunctionDef, ast.AsyncFunctionDef)
    base_parameters = {node.name: set(parameter_defaults(node))
                       for node in ast.walk(base_tree) if isinstance(node, function_types)}
    base_fields = {node.name: set(class_field_defaults(node))
                   for node in ast.walk(base_tree) if isinstance(node, ast.ClassDef)}
    leads = []
    for node in ast.walk(head_tree):
        if isinstance(node, ast.ClassDef) and node.name in base_fields:
            for name, (line, default) in class_field_defaults(node).items():
                if name not in base_fields[node.name] and is_option_default(default):
                    leads.append((line,
                                  "new-option",
                                  f"`{node.name}` gains `{name} = {ast.unparse(default)}`: should both paths exist?"))
        if not isinstance(node, function_types) or node.name not in base_parameters:
            continue
        for name, default in parameter_defaults(node).items():
            if name not in base_parameters[node.name] and is_option_default(default):
                leads.append((node.lineno,
                              "new-option",
                              f"`{node.name}` gains `{name}={ast.unparse(default)}`: should both paths exist?"))
    return leads


def python_leads(path: str,
                 source: str,
                 added: set[int],
                 callables: set[str],
                 base_source: str | None) -> list[tuple[int, str, str]]:
    """Leads from the AST and the comment tokens of one Python file."""
    leads = []
    tree = ast.parse(source)
    leads += option_leads(base_source=base_source, head_tree=tree)
    module_doc = ast.get_docstring(tree)
    if module_doc and PurePosixPath(path).name != "__init__.py" and tree.body[0].lineno in added:
        leads.append((tree.body[0].lineno, "module-docstring", "module opens with a docstring"))

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.lineno in added:
            doc = ast.get_docstring(node) or ""
            sections = {match.group(1) for match in DOCSTRING_SECTION.finditer(doc)}
            if sections and "Returns" not in sections and "Yields" not in sections and returns_value(node):
                leads.append((node.lineno, "docstring-no-returns", f"`{node.name}` has sections but no Returns"))
            for section in sections & {"Raises", "Warns"}:
                leads.append((node.lineno, "docstring-raises-warns", f"`{node.name}` has a {section} section"))
            if HISTORY_WORDS.search(doc):
                leads.append((node.lineno, "history-wording", f"`{node.name}` docstring: {HISTORY_WORDS.search(doc).group(0)!r}"))
        if isinstance(node, ast.Call) and node.lineno in added:
            name = callee_name(node)
            positional = [arg for arg in node.args if not isinstance(arg, ast.Starred)]
            if name in callables and positional and (len(positional) >= 2 or node.keywords):
                leads.append((node.lineno, "positional-argument", f"`{name}` gets {len(positional)} positional argument(s)"))
        if isinstance(node, ast.ImportFrom) and node.module == "__future__" and node.lineno in added:
            leads.append((node.lineno, "future-import", "from __future__ import"))

    if module_doc and HISTORY_WORDS.search(module_doc) and tree.body[0].lineno in added:
        leads.append((tree.body[0].lineno, "history-wording", f"module docstring: {HISTORY_WORDS.search(module_doc).group(0)!r}"))

    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        line = token.start[0]
        if token.type != tokenize.COMMENT or line not in added:
            continue
        if SECTION_DIVIDER.match(token.string):
            leads.append((line, "section-divider", token.string.strip()[:60]))
        elif match := HISTORY_WORDS.search(token.string):
            leads.append((line, "history-wording", f"comment: {match.group(0)!r}"))
    return leads


def text_leads(source: str, added: set[int], is_yaml: bool) -> list[tuple[int, str, str]]:
    """Leads from any text file: non-ASCII, and history wording in yaml comments."""
    leads = []
    for number, line in enumerate(source.splitlines(), start=1):
        if number not in added:
            continue
        if any(ord(character) > 127 for character in line):
            leads.append((number, "non-ascii", line.strip()[:60]))
        if is_yaml and line.lstrip().startswith("#") and (match := HISTORY_WORDS.search(line)):
            leads.append((number, "history-wording", f"yaml comment: {match.group(0)!r}"))
    return leads


def mirrored_test_path(path: str) -> str | None:
    """Expected test file for a new source module: src/<pkg>/a/b.py -> tests/a/test_b.py."""
    parts = PurePosixPath(path).parts
    if len(parts) < 3 or parts[0] != "src" or not path.endswith(".py") or parts[-1] == "__init__.py":
        return None
    return str(PurePosixPath("tests", *parts[2:-1], f"test_{parts[-1]}"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", required=True, help="path to the git checkout holding the refs")
    parser.add_argument("--base", required=True, help="base ref, e.g. origin/main")
    parser.add_argument("--head", required=True, help="head ref, e.g. origin/feature")
    args = parser.parse_args()

    added = added_lines(repo=args.repo, base=args.base, head=args.head)
    callables = project_callables(repo=args.repo, head=args.head)
    head_files = set(git(args.repo, "ls-tree", "-r", "--name-only", args.head).splitlines())
    new_files = set(git(args.repo, "diff", "--name-only", "--diff-filter=A", f"{args.base}...{args.head}").splitlines())

    rows = []
    for path, lines in sorted(added.items()):
        source = git(args.repo, "show", f"{args.head}:{path}")
        leads = text_leads(source=source, added=lines, is_yaml=path.endswith((".yaml", ".yml")))
        if path.endswith(".py"):
            skip_options = path in new_files or path.startswith("tests/")
            base_source = None if skip_options else git_or_none(args.repo, "show", f"{args.base}:{path}")
            leads += python_leads(path=path,
                                  source=source,
                                  added=lines,
                                  callables=callables,
                                  base_source=base_source)
        rows += [(path, line, rule, detail) for line, rule, detail in leads]

    for path in sorted(new_files):
        expected = mirrored_test_path(path)
        if expected and expected not in head_files:
            rows.append((path, 1, "no-mirrored-test", f"expected {expected}"))

    for path, line, rule, detail in sorted(rows):
        print(f"{path}:{line}\t{rule}\t{detail}")
    print(f"\n{len(rows)} lead(s). Each is unverified until checked against the rules file.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
