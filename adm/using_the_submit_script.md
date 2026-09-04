# Using `cse4001_submit.py`

`cse4001_submit.py` automates the procedure in [submitting_assignments.md](submitting_assignments.md). 

**Requirements:** `git` and `python3`.
**Optional but recommended:** the [GitHub CLI](https://cli.github.com) (`gh`).
With `gh` installed and logged in (`gh auth login`), the script creates the
private repository, adds the instructor and TA as collaborators, and verifies
that the repository is private and is not a fork. Without `gh` it prints the
steps for you to do on github.com and checks everything it can locally.

You can run it inside the CSE4001 container or on your own machine -- it only
needs `git` and `python3`.

---

## 1. Set up a new assignment

From `/root/workspace/` in the container (or any folder on your machine):

```shell
python3 cse4001_submit.py setup \
    --assignment os161-install \
    --netid jdoe2026 \
    --starter https://github.com/cse4001/install-the-cse4001-docker-assignment.git
```

Leave any option out and the script asks for it. Omit `--starter` when the
assignment has no starter code, or use `--here` to turn a folder you have
already been working in into the submission repository.

The script then:

1. creates (or asks you to create) the private repo `cse4001-os161-install-jdoe2026`;
2. clones the starter code and **deletes its `.git`**, so your submission is a
   fresh repository and not a fork;
3. adds the required `README.md` header with your name and NetID;
4. makes the first commit and pushes it to `main`;
5. invites `eraldoribeiro` and `hatemphd` as collaborators;
6. runs the final checklist.

> If you are asked for a password when pushing, GitHub wants a
> **Personal Access Token**, not your account password:
> <https://github.com/settings/tokens> (scope: `repo`).

## 2. Work, then submit

Edit your files as usual, then:

```shell
python3 cse4001_submit.py submit -m "Part 2 finished"
```

This commits everything, pushes it, and re-runs the checklist. Run it as often
as you like -- your submission time is the timestamp of your **last push**, so
push before the deadline.

You can run `submit` and `check` from inside the assignment folder **or** from
the folder above it (where you keep the script) -- it finds the assignment
repository on its own. If you keep several assignments side by side, say which
one with `-d`:

```shell
python3 cse4001_submit.py submit -d cse4001-os161-install-jdoe2026 -m "Part 2 finished"
```

## 3. Check before the deadline

```shell
python3 cse4001_submit.py check
```

Reports on: repository name, private visibility, fork status, collaborators,
the `README.md` header, uncommitted changes, and unpushed commits. It changes
nothing and exits with status 1 if anything still needs attention.

## Other commands

| Command | What it does |
| --- | --- |
| `readme` | Insert or fill in the required `README.md` header |
| `--dry-run` | Print what would happen without changing anything |
| `--yes` | Answer yes to every confirmation |
| `--help` | Full option list |

## Finally

Submit **only the repository URL** on Canvas:

```
https://github.com/<username>/cse4001-<assignment-name>-<netid>
```
