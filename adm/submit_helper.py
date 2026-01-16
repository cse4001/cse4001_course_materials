#!/usr/bin/env python3
import textwrap
import sys

def ask(prompt, default=None):
    if default:
        val = input(f"{prompt} [{default}]: ").strip()
        return val if val else default
    return input(f"{prompt}: ").strip()

print("\nCSE4001 Assignment Submission Helper\n")

name = ask("Student name")
netid = ask("NetID (e.g. jdoe2026)")
github = ask("GitHub username")
assignment = ask("Assignment name (e.g. os161-install)")
use_starter = ask("Use starter code? (y/n)", "y").lower() == "y"

course_org = "course-org"
starter_repo = None
if use_starter:
    starter_repo = ask("Starter repository name")

repo_name = f"cse4001-{assignment}-{netid}"
repo_url = f"https://github.com/{github}/{repo_name}"

print("\n--- Repository Info ---")
print("Repository name:", repo_name)
print("Repository URL:", repo_url)

print("\n--- Git Commands ---")
if use_starter:
    print(textwrap.dedent(f"""
        git clone https://github.com/{course_org}/{starter_repo}.git
        cd {starter_repo}
        rm -rf .git

        git init
        git add .
        git commit -m "Initial commit from assignment starter code"
        git branch -M main
        git remote add origin {repo_url}.git
        git push -u origin main
    """))
else:
    print(textwrap.dedent(f"""
        git init
        git add .
        git commit -m "Initial commit"
        git branch -M main
        git remote add origin {repo_url}.git
        git push -u origin main
    """))

print("\n--- Add the following to the repository's README.md ---")
print(textwrap.dedent(f"""

**Name:** {name}  
**NetID:** {netid}

...
"""))

print("\n--- Required Collaborators ---")
print("Instructor: eraldoribeiro")
print("TA: hatemphd")

print("\n--- Canvas Submission URL ---")
print(repo_url)

print("\nFinal checklist:")
print("[ ] Repo is private")
print("[ ] Collaborators added")
print("[ ] README completed")
print("[ ] Code pushed before deadline")


