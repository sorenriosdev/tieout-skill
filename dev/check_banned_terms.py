#!/usr/bin/env python3
"""Fail if any banned term appears in the repo, its staged changes or its history.

The terms list is never committed. It may live outside the repository, or
inside it only if git ignores it. Lookup order:
  1. $TIEOUT_BANNED_TERMS
  2. private-context/banned-terms.txt (inside the repo root, git-ignored)

Terms file format: one term per line; blank lines and lines starting with '#'
are ignored. Matching is substring-based, case-insensitive and accent-insensitive.
Matches are reported as location + term number, never the term itself.

Usage:
  check_banned_terms.py --staged          # pre-commit: staged content and paths
  check_banned_terms.py --message FILE    # commit-msg: the commit message
  check_banned_terms.py --tree            # tracked + untracked (not ignored) files
  check_banned_terms.py --file PATH ...   # any file(s), inside or outside a repository
  check_banned_terms.py --history         # every commit on every ref: diffs, paths,
                                          # messages, author/committer, ref names
Exit codes: 0 clean, 1 matches found, 2 configuration error.
"""
import argparse
import os
import pathlib
import subprocess
import sys
import unicodedata


def fail(msg):
    print(f"banned-terms: {msg}", file=sys.stderr)
    sys.exit(2)


def git(*args, check=True):
    out = subprocess.run(["git", *args], capture_output=True, check=check)
    return out.stdout


def repo_root():
    try:
        return pathlib.Path(git("rev-parse", "--show-toplevel").decode().strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None  # not in a git repository: only --file with an explicit terms list works


def normalize(text):
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


def load_terms(root):
    env = os.environ.get("TIEOUT_BANNED_TERMS")
    if not env and root is None:
        fail("not in a git repository and TIEOUT_BANNED_TERMS is not set. Point it at your terms file.")
    path = pathlib.Path(env) if env else root / "private-context" / "banned-terms.txt"
    path = path.resolve()
    if not path.is_file():
        fail(f"terms file not found at {path}. Refusing to continue (fail closed).")
    if root is not None and path.is_relative_to(root):
        ignored = subprocess.run(["git", "check-ignore", "-q", str(path)], cwd=root).returncode == 0
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", str(path)], cwd=root,
                                 capture_output=True).returncode == 0
        if not ignored or tracked:
            fail(f"terms file {path} is inside the repository and not git-ignored (or already tracked).")
    terms = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            terms.append(normalize(line))
    if not terms:
        fail(f"{path} has no terms. Refusing to continue (fail closed).")
    return terms


def scan(label, text, terms, hits):
    for n, line in enumerate(text.splitlines(), 1):
        norm = normalize(line)
        for i, term in enumerate(terms, 1):
            if term in norm:
                hits.append(f"{label}:{n}: term #{i}")


def decode(data):
    return data.decode("utf-8", errors="replace")


def check_staged(terms, hits):
    names = decode(git("diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR")).split("\0")
    for name in filter(None, names):
        scan(f"path {name}", name, terms, hits)
        scan(name, decode(git("show", f":{name}")), terms, hits)


def check_tree(root, terms, hits):
    names = decode(git("ls-files", "-z", "--cached", "--others", "--exclude-standard")).split("\0")
    for name in filter(None, names):
        scan(f"path {name}", name, terms, hits)
        f = root / name
        if f.is_file():
            scan(name, decode(f.read_bytes()), terms, hits)


def check_history(terms, hits):
    if not git("rev-parse", "--verify", "-q", "HEAD", check=False):
        return
    fmt = "--format=commit %H%nauthor %an <%ae>%ncommitter %cn <%ce>%n%n%B"
    for sha in decode(git("rev-list", "--all")).split():
        text = decode(git("show", "--no-color", "-p", "--stat", fmt, sha))
        scan(f"commit {sha[:10]}", text, terms, hits)
    scan("refs", decode(git("for-each-ref", "--format=%(refname)")), terms, hits)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--staged", action="store_true")
    ap.add_argument("--tree", action="store_true")
    ap.add_argument("--history", action="store_true")
    ap.add_argument("--message", metavar="FILE")
    ap.add_argument("--file", metavar="PATH", nargs="+", help="scan these files (works outside a repository)")
    args = ap.parse_args()
    if not (args.staged or args.tree or args.history or args.message or args.file):
        ap.error("choose at least one of --staged, --tree, --history, --message, --file")
    git_only = args.staged or args.tree or args.history
    if git_only and repo_root() is None:
        ap.error("--staged, --tree and --history need a git repository")

    root = repo_root()
    terms = load_terms(root)
    hits = []
    if args.staged:
        check_staged(terms, hits)
    if args.message:
        scan("commit message", pathlib.Path(args.message).read_text(encoding="utf-8"), terms, hits)
    for f in args.file or []:
        fp = pathlib.Path(f)
        if not fp.is_file():
            fail(f"not a file: {fp}")
        scan(fp.name, fp.read_text(encoding="utf-8", errors="replace"), terms, hits)
    if args.tree:
        check_tree(root, terms, hits)
    if args.history:
        check_history(terms, hits)

    if hits:
        print(f"banned-terms: {len(hits)} match(es):", file=sys.stderr)
        for h in hits:
            print("  " + h, file=sys.stderr)
        sys.exit(1)
    scopes = [s for s in ("staged", "message", "tree", "history", "file") if getattr(args, s)]
    print(f"banned-terms: 0 matches ({', '.join(scopes)}; {len(terms)} terms)")


if __name__ == "__main__":
    main()
