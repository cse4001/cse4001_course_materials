# Submitting Assignments Using GitHub (CSE4001)

In this course, programming assignments are submitted using **GitHub**.

------

## 1. Submission platform

All assignments must be submitted via **GitHub repositories**.

- Each student (or team for group assignments) submits **one private repository per assignment**
- ZIP files, screenshots-only submissions, or email submissions are **not accepted**

------

## 2. Repository creation (REQUIRED)

For each assignment, students must create a **new private GitHub repository** under their personal GitHub account.

> ⚠️ **Important:** Git does *not* create GitHub repositories automatically.
>  You must create the repository on GitHub **before** pushing code.

### Repository naming convention

```
cse4001-<assignment-name>-<netid>
```

- `<netid>` is your FIT Tracks username

**Example**

```
cse4001-os161-install-jdoe2026
```

### Repository requirements

- Visibility: **Private**
- Initialize with a `README.md`
- Contains only files relevant to the assignment

------

## 3. Starter code procedure (when provided)

❌ **Do NOT fork** the assignment repository
 ❌ **Do NOT submit a forked repository**

Instead:

1. Clone the starter repository
2. Create your **own private repository** on GitHub (Follow the name convension: `cse4001-<assignment-name>-<netid>`)
4. Copy the starter files into your repository
5. Commit the starter code as an initial commit

------

## 4. Recommended Git workflow

Run the following **after creating your private repository on GitHub**:

```
git clone https://github.com/<course-org>/<assignment-starter>.git
cd <assignment-starter>
rm -rf .git

git init
git add .
git commit -m "Initial commit from assignment starter code"
git branch -M main
git remote add origin https://github.com/<username>/cse4001-<assignment-name>-<netid>.git
git push -u origin main
```

If prompted for a password, use a **GitHub Personal Access Token** (not your GitHub password).

------

## 5. Collaborators (REQUIRED)

Students **must** add the instructor and all TAs as collaborators.

### Required collaborators

- **Instructor:** `eraldoribeiro`
- **Teaching Assistant:** `hatemphd`

> ⚠️ Repositories without correct collaborator access **will not be graded**.

------

## 6. Assignment content requirements

Each repository must include:

- ✅ All required source code
- ✅ Required screenshots or logs (PNG / JPG / TXT)
- ✅ A completed `README.md` containing:
  - Student name
  - NetID
  - Assignment description
  - Build/run instructions
  - Notes or assumptions

### README template

```
# CSE4001 – Assignment <N>

**Name:** Jane Doe  
**NetID:** jdoe2026

## Description
Brief description of the assignment.

## Build Instructions
...

## Run Instructions
...

## Notes
...
```

------

## 7. Submitting the assignment

On **Canvas**, submit **only** the URL of your GitHub repository:

```
https://github.com/<username>/cse4001-<assignment-name>-<netid>
```

No additional uploads unless explicitly requested.

------

## 8. Deadlines & late policy

- Submission time is determined by the **timestamp of the last pushed commit**
- Late submissions follow the course late policy

------

## 9. Academic integrity

- All submitted work must be **your own**
- Repositories must remain **private**
- Standard university academic integrity policies apply

------

## 10. Common reasons assignments are not graded

- Repository is public
- Instructor or TA not added as collaborator
- Incorrect repository name
- Forked repository submitted
- Missing README or required files
- Work not pushed before the deadline

------

## 11. Final submission checklist

- [ ]  Repository name is correct
- [ ]  Repository is private
- [ ]  Instructor and TA added
- [ ]  Code builds and runs
- [ ]  README completed
- [ ]  All changes pushed

## 
