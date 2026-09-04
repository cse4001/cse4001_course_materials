#!/usr/bin/env python3
"""
cse4001_submit.py -- assignment submission helper for CSE4001 (Operating Systems Concepts).

Automates the submission procedure described in adm/submitting_assignments.md:

  setup    Create the private GitHub repo, import the starter code, add the
           instructor and TA as collaborators, and push the first commit.
  submit   Commit and push your work, then re-run the submission checklist.
  check    Run the final checklist against your repository (no changes made).
  readme   Insert / fill in the required README.md header.

Requires: Python 3.6+, git.
Optional: the GitHub CLI `gh` (https://cli.github.com).  With `gh` installed
and authenticated the script can create the repository and add collaborators
for you, and can verify privacy / fork / collaborator status.  Without it the
script prints the exact steps to do by hand on github.com.

Examples
--------
    python3 cse4001_submit.py setup \
        --assignment os161-install --netid jdoe2026 \
        --starter https://github.com/cse4001/install-the-cse4001-docker-assignment.git

    python3 cse4001_submit.py submit -m "Part 2 finished"
    python3 cse4001_submit.py check
"""

from __future__ import print_function

import argparse
import json
import os
import re
import shutil
import subprocess
import sys

COURSE = "cse4001"
INSTRUCTOR = "eraldoribeiro"
TAS = ["hatemphd"]
COLLABORATORS = [INSTRUCTOR] + TAS
DEFAULT_BRANCH = "main"
CONFIG_NAME = ".cse4001-submit.json"

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

README_TEMPLATE = """# CSE4001 - {title}

**Name:** {name}
**NetID:** {netid}

## Description
Brief description of the assignment.

## Build Instructions
...

## Run Instructions
...

## Notes
...
"""

PLACEHOLDERS = ["Jane Doe", "jdoe2026", "<N>", "Brief description of the assignment."]


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

class Fail(Exception):
    """Fatal, user-facing error."""


DRY_RUN = False


def c(text, color):
    if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
        return text
    codes = {"red": 31, "green": 32, "yellow": 33, "blue": 34, "bold": 1}
    return "\033[%dm%s\033[0m" % (codes[color], text)


def info(msg):
    print(msg)


def step(msg):
    print(c("\n==> " + msg, "bold"))


def ok(msg):
    print(c("  [ok]  ", "green") + msg)


def warn(msg):
    print(c("  [!]   ", "yellow") + msg)


def bad(msg):
    print(c("  [X]   ", "red") + msg)


def run(cmd, cwd=None, check=True, capture=True, quiet=False):
    """Run a command.  Returns (returncode, stdout, stderr)."""
    if not quiet:
        print(c("  $ " + " ".join(cmd), "blue") + ("" if cwd is None else "   (in %s)" % cwd))
    if DRY_RUN and _mutating(cmd):
        return 0, "", ""
    sys.stdout.flush()
    if capture:
        p = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, universal_newlines=True)
        out, err = p.stdout, p.stderr
    else:
        p = subprocess.run(cmd, cwd=cwd)
        out, err = "", ""
    if check and p.returncode != 0:
        raise Fail("command failed: %s\n%s%s" % (" ".join(cmd), out, err))
    return p.returncode, out, err


def _mutating(cmd):
    """True for commands that change something (skipped under --dry-run)."""
    if cmd[0] == "git":
        verb = cmd[3] if cmd[1] == "-C" else cmd[1]
        return verb in ("init", "add", "commit", "push", "pull", "remote", "branch",
                        "clone", "config", "checkout", "symbolic-ref")
    if cmd[0] == "gh":
        if cmd[1:3] == ["repo", "create"]:
            return True
        return cmd[1] == "api" and "-X" in cmd
    return True


def have(prog):
    return shutil.which(prog) is not None


def ask(prompt, default=None, required=True):
    suffix = " [%s]: " % default if default else ": "
    while True:
        try:
            answer = input(prompt + suffix).strip()
        except EOFError:
            answer = ""
        if not answer and default is not None:
            return default
        if answer or not required:
            return answer
        print("  (a value is required)")


def confirm(prompt, default=False, assume_yes=False):
    if assume_yes:
        print(prompt + " yes (--yes)")
        return True
    d = "Y/n" if default else "y/N"
    try:
        answer = input("%s [%s] " % (prompt, d)).strip().lower()
    except EOFError:
        return default
    if not answer:
        return default
    return answer in ("y", "yes")


def slug(value):
    return re.sub(r"[^a-z0-9-]+", "-", value.strip().lower()).strip("-")


# --------------------------------------------------------------------------
# configuration (remembered between runs)
# --------------------------------------------------------------------------

def config_path(repo_dir):
    return os.path.join(repo_dir, CONFIG_NAME)


def load_config(repo_dir):
    path = config_path(repo_dir)
    if os.path.isfile(path):
        try:
            with open(path) as fh:
                return json.load(fh)
        except ValueError:
            return {}
    return {}


def save_config(repo_dir, cfg):
    if DRY_RUN:
        return
    with open(config_path(repo_dir), "w") as fh:
        json.dump(cfg, fh, indent=2, sort_keys=True)
        fh.write("\n")
    # keep the helper's bookkeeping file out of the submission
    ignore = os.path.join(repo_dir, ".gitignore")
    lines = []
    if os.path.isfile(ignore):
        with open(ignore) as fh:
            lines = fh.read().splitlines()
    if CONFIG_NAME not in lines:
        with open(ignore, "a") as fh:
            if lines and lines[-1].strip():
                fh.write("\n")
            fh.write(CONFIG_NAME + "\n")


# --------------------------------------------------------------------------
# github helpers
# --------------------------------------------------------------------------

def gh_ready():
    """True if `gh` is installed and logged in."""
    if not have("gh"):
        return False
    code, _, _ = run(["gh", "auth", "status"], check=False, quiet=True)
    return code == 0


def gh_user():
    code, out, _ = run(["gh", "api", "user", "-q", ".login"], check=False, quiet=True)
    return out.strip() if code == 0 else ""


def gh_repo_json(full_name, fields):
    code, out, _ = run(["gh", "repo", "view", full_name, "--json", ",".join(fields)],
                       check=False, quiet=True)
    if code != 0:
        return None
    try:
        return json.loads(out)
    except ValueError:
        return None


def gh_collaborator_state(full_name, login):
    """Return 'collaborator', 'invited', 'absent' or 'unknown'."""
    code, out, _ = run(["gh", "api", "repos/%s/collaborators/%s" % (full_name, login)],
                       check=False, quiet=True)
    if code == 0:
        return "collaborator"
    code, out, _ = run(["gh", "api", "repos/%s/invitations" % full_name,
                        "-q", "[.[].invitee.login]"], check=False, quiet=True)
    if code == 0:
        try:
            if login.lower() in [x.lower() for x in json.loads(out or "[]")]:
                return "invited"
        except ValueError:
            pass
        return "absent"
    return "unknown"


def add_collaborators(full_name, assume_yes=False):
    """Invite the instructor and TAs.  Returns True if all invitations were sent."""
    if not gh_ready():
        warn("gh is not available -- add collaborators by hand:")
        info("        https://github.com/%s/settings/access" % full_name)
        info("        invite: %s" % ", ".join(COLLABORATORS))
        return False
    all_good = True
    for login in COLLABORATORS:
        state = gh_collaborator_state(full_name, login)
        if state in ("collaborator", "invited"):
            ok("%s is already a %s" % (login, state))
            continue
        if not confirm("  Invite %s as a collaborator on %s?" % (login, full_name),
                       default=True, assume_yes=assume_yes):
            warn("skipped %s -- the repository will not be graded without it" % login)
            all_good = False
            continue
        code, out, err = run(["gh", "api", "-X", "PUT",
                              "repos/%s/collaborators/%s" % (full_name, login),
                              "-f", "permission=push"], check=False)
        if code == 0:
            ok("invited %s" % login)
        else:
            bad("could not invite %s: %s" % (login, (err or out).strip()))
            all_good = False
    return all_good


# --------------------------------------------------------------------------
# git helpers
# --------------------------------------------------------------------------

def is_repo(path):
    code, _, _ = run(["git", "-C", path, "rev-parse", "--is-inside-work-tree"],
                     check=False, quiet=True)
    return code == 0


def repo_root(path="."):
    code, out, _ = run(["git", "-C", path, "rev-parse", "--show-toplevel"],
                       check=False, quiet=True)
    return out.strip() if code == 0 else None


def git_out(repo_dir, *args):
    code, out, _ = run(["git", "-C", repo_dir] + list(args), check=False, quiet=True)
    return out.strip() if code == 0 else ""


def ensure_identity(repo_dir, assume_yes=False):
    """git commit fails without user.name / user.email (common in a fresh container)."""
    if DRY_RUN:
        return
    name = git_out(repo_dir, "config", "user.name")
    email = git_out(repo_dir, "config", "user.email")
    if name and email:
        return
    step("git needs to know who you are")
    if not name:
        name = ask("  Your full name")
        run(["git", "-C", repo_dir, "config", "user.name", name])
    if not email:
        email = ask("  Your e-mail address")
        run(["git", "-C", repo_dir, "config", "user.email", email])


def remote_url(repo_dir, name="origin"):
    """The configured URL of a remote (raw: url.*.insteadOf is not applied)."""
    return git_out(repo_dir, "config", "--get", "remote.%s.url" % name)


def parse_remote(url):
    """Return (owner, repo) from an https or ssh GitHub URL, or (None, None)."""
    m = re.search(r"github\.com[:/]+([^/]+)/([^/]+?)(?:\.git)?/?$", url or "")
    if not m:
        return None, None
    return m.group(1), m.group(2)


# --------------------------------------------------------------------------
# names
# --------------------------------------------------------------------------

def repo_name(assignment, netid):
    return "%s-%s-%s" % (COURSE, assignment, netid)


def validate_names(assignment, netid):
    for label, value in (("assignment name", assignment), ("NetID", netid)):
        if not NAME_RE.match(value):
            raise Fail("invalid %s %r: use lowercase letters, digits and hyphens only"
                       % (label, value))


# --------------------------------------------------------------------------
# README
# --------------------------------------------------------------------------

def readme_path(repo_dir):
    for candidate in ("README.md", "readme.md", "README.MD"):
        p = os.path.join(repo_dir, candidate)
        if os.path.isfile(p):
            return p
    return os.path.join(repo_dir, "README.md")


def write_readme(repo_dir, cfg, assume_yes=False):
    path = readme_path(repo_dir)
    existing = ""
    if os.path.isfile(path):
        with open(path) as fh:
            existing = fh.read()

    name = cfg.get("name") or ask("  Your full name")
    netid = cfg.get("netid") or ask("  Your NetID")
    title = cfg.get("assignment", "Assignment").replace("-", " ")
    cfg["name"] = name

    header = README_TEMPLATE.format(title=title, name=name, netid=netid)

    if existing.strip():
        if re.search(r"^\s*\*\*NetID:\*\*\s*\S", existing, re.M):
            ok("README.md already carries a Name / NetID header")
            return path
        if not confirm("  Prepend the required header to the existing README.md?",
                       default=True, assume_yes=assume_yes):
            return path
        new = header.rstrip() + "\n\n---\n\n" + existing.lstrip()
    else:
        new = header

    if not DRY_RUN:
        with open(path, "w") as fh:
            fh.write(new)
    ok("wrote %s" % os.path.relpath(path, repo_dir))
    return path


def readme_problems(repo_dir, cfg=None):
    """Return (errors, warnings) for the assignment README."""
    cfg = cfg or {}
    path = readme_path(repo_dir)
    if not os.path.isfile(path):
        return ["README.md is missing"], []
    with open(path) as fh:
        text = fh.read()
    errors, warnings = [], []
    if not re.search(r"\*\*Name:\*\*\s*\S", text):
        errors.append("README.md has no filled-in **Name:** line")
    if not re.search(r"\*\*NetID:\*\*\s*\S", text):
        errors.append("README.md has no filled-in **NetID:** line")
    mine = [v for v in (cfg.get("name"), cfg.get("netid")) if v]
    left = [p for p in PLACEHOLDERS if p in text and p not in mine]
    if left:
        warnings.append("README.md still contains template text (%s) -- fill in the "
                        "description and the build/run instructions before the deadline"
                        % ", ".join(repr(x) for x in left))
    return errors, warnings


# --------------------------------------------------------------------------
# command: setup
# --------------------------------------------------------------------------

def cmd_setup(args):
    step("CSE4001 assignment setup")

    assignment = slug(args.assignment or ask("  Assignment name (e.g. os161-install)"))
    netid = slug(args.netid or ask("  Your NetID (FIT Tracks username)"))
    validate_names(assignment, netid)

    user = args.github_user or (gh_user() if gh_ready() else "")
    user = user or ask("  Your GitHub username")
    name = repo_name(assignment, netid)
    full = "%s/%s" % (user, name)
    url = "https://github.com/%s.git" % full

    info("")
    info("  repository : " + c(full, "bold"))
    info("  visibility : private")
    info("  branch     : " + DEFAULT_BRANCH)

    # ---- 1. the repository on github.com -------------------------------
    step("1. Private repository on github.com")
    exists = False
    if gh_ready():
        data = gh_repo_json(full, ["name"])
        exists = data is not None
        if exists:
            ok("%s already exists" % full)
        elif confirm("  Create the private repository %s now?" % full,
                     default=True, assume_yes=args.yes):
            run(["gh", "repo", "create", full, "--private"], capture=False)
            ok("created %s" % full)
            exists = True
    if not exists:
        warn("create it by hand before continuing:")
        info("        1. https://github.com/new")
        info("        2. Repository name : %s" % name)
        info("        3. Visibility      : Private")
        info("        4. Tick 'Add a README file'")
        info("        5. Do NOT fork the starter repository")
        if not confirm("  Repository created?", default=False, assume_yes=args.yes):
            raise Fail("create the repository first, then run this command again")

    # ---- 2. local working copy -----------------------------------------
    step("2. Local working copy")
    if args.here:
        work = os.path.abspath(args.directory or ".")
        if not os.path.isdir(work):
            raise Fail("no such directory: %s" % work)
        info("  using the existing directory %s" % work)
    else:
        work = os.path.abspath(args.directory or name)
        if os.path.exists(work) and os.listdir(work):
            raise Fail("%s already exists and is not empty -- pass --directory or --here"
                       % work)
        if args.starter:
            run(["git", "clone", args.starter, work], capture=False)
        else:
            if not DRY_RUN:
                os.makedirs(work)
            ok("created empty directory %s" % work)

    # starter code must not keep its own history (that is what makes a fork-like
    # submission), so the .git directory is removed and the history restarted
    dotgit = os.path.join(work, ".git")
    if os.path.isdir(dotgit):
        origin = remote_url(work)
        if origin and parse_remote(origin)[1] == name:
            ok("this directory is already your own repository")
        else:
            info("  this directory carries the starter code's git history:")
            info("    %s" % (origin or "(no remote)"))
            if not confirm("  Delete %s and start a fresh history?" % dotgit,
                           default=True, assume_yes=args.yes):
                raise Fail("cannot continue while the starter history is present")
            if not DRY_RUN:
                shutil.rmtree(dotgit)
            ok("removed the starter code's .git")

    if not is_repo(work):
        run(["git", "init", work], capture=False)
        # `git branch -M` needs a commit on older git; this works on an empty repo
        run(["git", "-C", work, "symbolic-ref", "HEAD",
             "refs/heads/" + DEFAULT_BRANCH], check=False)

    cfg = load_config(work)
    cfg.update({"assignment": assignment, "netid": netid,
                "github_user": user, "repo": full})
    if args.name:
        cfg["name"] = args.name

    ensure_identity(work, args.yes)

    # ---- 3. README ------------------------------------------------------
    step("3. README.md")
    write_readme(work, cfg, args.yes)
    save_config(work, cfg)

    # ---- 4. first commit and push --------------------------------------
    step("4. First commit and push")
    if remote_url(work):
        current = remote_url(work)
        if parse_remote(current)[1] != name:
            run(["git", "-C", work, "remote", "set-url", "origin", url])
    else:
        run(["git", "-C", work, "remote", "add", "origin", url])
    ok("origin -> %s" % url)

    run(["git", "-C", work, "add", "-A"], capture=False)
    code, _, _ = run(["git", "-C", work, "diff", "--cached", "--quiet"], check=False, quiet=True)
    if code != 0:
        run(["git", "-C", work, "commit", "-m", args.message], capture=False)
    else:
        info("  nothing to commit")
    run(["git", "-C", work, "branch", "-M", DEFAULT_BRANCH], check=False)
    push(work, first=True, assume_yes=args.yes)

    # ---- 5. collaborators ----------------------------------------------
    step("5. Collaborators")
    add_collaborators(full, args.yes)

    # ---- 6. checklist ---------------------------------------------------
    failures = run_checks(work, cfg)
    print_summary(full, work, failures)


def push(repo_dir, first=False, assume_yes=False, _retry=True):
    cmd = ["git", "-C", repo_dir, "push"]
    if first:
        cmd += ["-u", "origin", DEFAULT_BRANCH]
    code, out, err = run(cmd, check=False, capture=False)
    if code != 0 and _retry:
        info("")
        if first:
            # the usual cause: the repository was created on github.com with a
            # README, so origin/main already has a commit.  The files here are
            # the submission, so conflicts are resolved in favour of this copy.
            info("  The push was rejected because %s already has a commit on"
                 % DEFAULT_BRANCH)
            info("  GitHub -- normally the README created by the web page.")
            question = ("  Combine it with your files (your versions win) and push again?")
            extra = ["--allow-unrelated-histories", "-X", "theirs"]
        else:
            info("  The push was rejected because GitHub has commits you do not")
            info("  have locally (did you edit files on github.com?).")
            question = "  Pull those commits into your copy and push again?"
            extra = []
        if confirm(question, default=True, assume_yes=assume_yes):
            rc, _, _ = run(["git", "-C", repo_dir, "pull", "--rebase"] + extra
                           + ["origin", DEFAULT_BRANCH], check=False, capture=False)
            if rc == 0:
                return push(repo_dir, first=first, assume_yes=assume_yes, _retry=False)
            # never leave the student sitting in a half-finished rebase
            run(["git", "-C", repo_dir, "rebase", "--abort"], check=False, quiet=True)
            warn("could not combine the two histories automatically -- your files "
                 "are untouched")
            info("        ask the instructor or TA, or create the repository again "
                 "on github.com")
            info("        WITHOUT ticking 'Add a README file' and run setup again")
    if code != 0:
        raise Fail(
            "push failed.\n"
            "  * If you were asked for a password, GitHub wants a Personal Access\n"
            "    Token instead: https://github.com/settings/tokens (scope: repo).\n"
            "  * If the remote already has commits (a README created on github.com),\n"
            "    run:  git -C %s pull --rebase origin %s   and push again."
            % (repo_dir, DEFAULT_BRANCH))
    ok("pushed to origin/%s" % DEFAULT_BRANCH)


# --------------------------------------------------------------------------
# finding the assignment repository
# --------------------------------------------------------------------------

def find_repo(explicit=None):
    """Locate the assignment repository.

    Looks at --directory, then the current directory, then one level down --
    the script is usually kept next to the assignment folder rather than
    inside it, so `submit` is often run from the parent directory.
    """
    if explicit:
        root = repo_root(explicit)
        if not root:
            raise Fail("%s is not a git repository" % explicit)
        return root

    root = repo_root(".")
    if root:
        return root

    candidates = []
    for entry in sorted(os.listdir(".")):
        path = os.path.abspath(entry)
        if not os.path.isdir(os.path.join(path, ".git")):
            continue
        if os.path.isfile(os.path.join(path, CONFIG_NAME)):
            candidates.append((2, path))          # set up by this script
        elif entry.startswith(COURSE + "-"):
            candidates.append((1, path))          # follows the naming convention
    best = [p for score, p in candidates if score == max(s for s, _ in candidates)] \
        if candidates else []

    if len(best) == 1:
        info("  using the assignment repository %s" % os.path.relpath(best[0]))
        return best[0]
    if len(best) > 1:
        raise Fail("several assignment repositories found here:\n    %s\n"
                   "  say which one, e.g.  -d %s"
                   % ("\n    ".join(os.path.relpath(p) for p in best),
                      os.path.relpath(best[0])))
    raise Fail("no assignment repository found in %s.\n"
               "  * cd into your assignment folder and run this again, or\n"
               "  * point at it with  -d <folder>, or\n"
               "  * run `setup` first if you have not created it yet"
               % os.path.abspath("."))


# --------------------------------------------------------------------------
# command: submit
# --------------------------------------------------------------------------

def cmd_submit(args):
    work = find_repo(args.directory)
    cfg = load_config(work)
    ensure_identity(work, args.yes)

    step("Committing your work")
    run(["git", "-C", work, "add", "-A"], capture=False)
    code, out, _ = run(["git", "-C", work, "status", "--short"], quiet=True)
    if out.strip():
        info(out.rstrip())
    code, _, _ = run(["git", "-C", work, "diff", "--cached", "--quiet"], check=False, quiet=True)
    if code == 0:
        info("  nothing new to commit")
    else:
        message = args.message or ask("  Commit message", default="Assignment work")
        run(["git", "-C", work, "commit", "-m", message], capture=False)

    step("Pushing to GitHub")
    upstream = git_out(work, "rev-parse", "--abbrev-ref", "@{upstream}")
    push(work, first=not upstream, assume_yes=args.yes)

    failures = run_checks(work, cfg)
    full = cfg.get("repo") or "/".join([x or "?" for x in parse_remote(remote_url(work))])
    print_summary(full, work, failures)


# --------------------------------------------------------------------------
# command: readme
# --------------------------------------------------------------------------

def cmd_readme(args):
    try:
        work = find_repo(args.directory)
    except Fail:
        work = os.path.abspath(args.directory or ".")
    cfg = load_config(work)
    if args.name:
        cfg["name"] = args.name
    if args.netid:
        cfg["netid"] = slug(args.netid)
    if args.assignment:
        cfg["assignment"] = slug(args.assignment)
    step("README.md")
    write_readme(work, cfg, args.yes)
    save_config(work, cfg)


# --------------------------------------------------------------------------
# command: check
# --------------------------------------------------------------------------

def cmd_check(args):
    work = find_repo(args.directory)
    cfg = load_config(work)
    failures = run_checks(work, cfg)
    full = cfg.get("repo") or "/".join([x or "?" for x in parse_remote(remote_url(work))])
    print_summary(full, work, failures)
    return 1 if failures else 0


def run_checks(work, cfg):
    """Run the final checklist.  Returns the number of failed items."""
    step("Final checklist")
    if DRY_RUN and not os.path.isdir(os.path.join(work, ".git")):
        info("  (skipped: nothing was actually created in this dry run)")
        return 0
    failures = 0

    origin = remote_url(work)
    owner, name = parse_remote(origin)
    full = "%s/%s" % (owner, name) if owner else None

    # 1. name
    expected = None
    if cfg.get("assignment") and cfg.get("netid"):
        expected = repo_name(cfg["assignment"], cfg["netid"])
    if not name:
        bad("no 'origin' remote -- nothing has been submitted yet")
        failures += 1
    elif expected and name != expected:
        bad("repository is named %s, expected %s" % (name, expected))
        failures += 1
    elif not re.match(r"^%s-[a-z0-9-]+-[a-z0-9-]+$" % COURSE, name):
        bad("repository name %r does not follow cse4001-<assignment-name>-<netid>" % name)
        failures += 1
    else:
        ok("repository name: %s" % name)

    # 2-4. server-side facts (need gh)
    if full and gh_ready():
        data = gh_repo_json(full, ["isPrivate", "isFork", "url"])
        if data is None:
            bad("cannot read %s -- does it exist and do you have access?" % full)
            failures += 1
        else:
            if data.get("isPrivate"):
                ok("repository is private")
            else:
                bad("repository is PUBLIC -- make it private in Settings")
                failures += 1
            if data.get("isFork"):
                bad("this is a FORK -- forked repositories are not accepted")
                failures += 1
            else:
                ok("not a fork")
            for login in COLLABORATORS:
                state = gh_collaborator_state(full, login)
                if state == "collaborator":
                    ok("collaborator: %s" % login)
                elif state == "invited":
                    ok("collaborator: %s (invitation pending)" % login)
                elif state == "absent":
                    bad("%s is NOT a collaborator -- the repo will not be graded" % login)
                    failures += 1
                else:
                    warn("could not check collaborator %s" % login)
    elif full:
        warn("gh is not installed/authenticated -- check these by hand:")
        info("        private + not a fork : https://github.com/%s" % full)
        info("        collaborators (%s) : https://github.com/%s/settings/access"
             % (", ".join(COLLABORATORS), full))

    # 5. README
    errors, warnings = readme_problems(work, cfg)
    if not errors:
        ok("README.md has the required header")
    for p in errors:
        bad(p)
    failures += len(errors)
    for p in warnings:
        warn(p)

    # 6. everything committed
    dirty = git_out(work, "status", "--porcelain")
    if dirty:
        bad("uncommitted changes:")
        for line in dirty.splitlines():
            info("        " + line.strip())
        failures += 1
    else:
        ok("working tree is clean")

    # 7. everything pushed
    upstream = git_out(work, "rev-parse", "--abbrev-ref", "@{upstream}")
    if not upstream:
        bad("branch has no upstream -- nothing pushed yet")
        failures += 1
    else:
        run(["git", "-C", work, "fetch", "--quiet"], check=False, quiet=True)
        ahead = git_out(work, "rev-list", "--count", "%s..HEAD" % upstream)
        if ahead and ahead != "0":
            bad("%s commit(s) not pushed -- run `submit`" % ahead)
            failures += 1
        else:
            ok("all commits pushed")
            last = git_out(work, "log", "-1", "--format=%cd", "--date=iso")
            if last:
                info("        last commit (this is your submission time): %s" % last)

    # 8. leftover starter checkout
    for entry in sorted(os.listdir(work) if os.path.isdir(work) else []):
        sub = os.path.join(work, entry)
        if os.path.isdir(sub) and os.path.isdir(os.path.join(sub, ".git")):
            warn("%s/ contains its own .git -- remove the starter-code copy so it "
                 "is not confused with your submission" % entry)

    print("")
    if failures:
        print(c("  %d item(s) still need attention." % failures, "red"))
    else:
        print(c("  All checks passed.", "green"))
    return failures


def next_command(work):
    """A copy-pasteable `submit` command for this repository."""
    script = os.path.abspath(__file__)
    try:
        rel_script = os.path.relpath(script)
        if not rel_script.startswith(os.path.join("..", "..")):
            script = rel_script
        rel = os.path.relpath(work)
    except ValueError:
        rel = work
    where = "" if rel == "." else " -d %s" % rel
    return 'python3 %s submit%s -m "what you changed"' % (script, where)


def print_summary(full, work, failures=0):
    print("")
    if failures:
        print(c("Not ready to submit yet -- fix the [X] items above, then run:", "yellow"))
        print("    " + next_command(work))
        print("")
        print("When every check passes, submit this URL on Canvas:")
        print("    https://github.com/%s" % full)
        print("")
        print("Local copy: %s" % work)
        return
    print(c("Submit this URL on Canvas:", "bold"))
    print("    https://github.com/%s" % full)
    print("")
    print("Local copy: %s" % work)
    print("")
    print("Next time you change something, run:")
    print("    " + next_command(work))


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(
        prog="cse4001_submit.py",
        description="Submit CSE4001 assignments through GitHub.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Examples")[-1])
    p.add_argument("--dry-run", action="store_true",
                   help="show what would happen without changing anything")
    p.add_argument("-y", "--yes", action="store_true",
                   help="answer yes to every confirmation")
    sub = p.add_subparsers(dest="command")

    s = sub.add_parser("setup", help="create the repo, import starter code, push")
    s.add_argument("-a", "--assignment", help="assignment name, e.g. os161-install")
    s.add_argument("-n", "--netid", help="your FIT Tracks username")
    s.add_argument("-u", "--github-user", help="your GitHub username")
    s.add_argument("--name", help="your full name (for README.md)")
    s.add_argument("--starter", help="URL of the starter-code repository")
    s.add_argument("-d", "--directory", help="where to put the local working copy")
    s.add_argument("--here", action="store_true",
                   help="use an existing directory instead of cloning the starter")
    s.add_argument("-m", "--message", default="Initial commit from assignment starter code")
    s.set_defaults(func=cmd_setup)

    s = sub.add_parser("submit", help="commit, push and re-check")
    s.add_argument("-m", "--message", help="commit message")
    s.add_argument("-d", "--directory", help="assignment directory (default: current)")
    s.set_defaults(func=cmd_submit)

    s = sub.add_parser("check", help="run the final checklist only")
    s.add_argument("-d", "--directory", help="assignment directory (default: current)")
    s.set_defaults(func=cmd_check)

    s = sub.add_parser("readme", help="insert / fill the required README header")
    s.add_argument("-d", "--directory")
    s.add_argument("--name")
    s.add_argument("-n", "--netid")
    s.add_argument("-a", "--assignment")
    s.set_defaults(func=cmd_readme)
    return p


def main(argv=None):
    global DRY_RUN
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    DRY_RUN = args.dry_run
    if DRY_RUN:
        warn("dry run -- no files, commits or GitHub state will be changed")
    if not have("git"):
        bad("git is not installed")
        return 1
    try:
        return args.func(args) or 0
    except Fail as exc:
        print("")
        print(c("Error: ", "red") + str(exc))
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
