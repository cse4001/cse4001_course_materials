# Submitting assignments using GitHub

In this course, programming assignments (and also some other assignments) are submitted using **GitHub**. 

## 1. Submission platform

All assignments must be submitted via **GitHub repositories**.

- Each student (or team for group assignments) submits **one private repository per assignment**
- ZIP files, screenshots-only submissions, or email submissions are **not accepted**.

------

## 2. Repository creation

For each assignment, students must create a **new private GitHub repository** under their personal GitHub account.

### Repository naming convention

```
cse4001-<assignment-name>-<netid>
```

Here, `<netid>` is the student's FIT tracks username. 

**Example**

```
cse4001-os161-install-jdoe2026
```

### Repository requirements

- Visibility: **Private**
- Initialized with a `README.md`
- Contains only files relevant to the assignment

------

## 3. Starter code procedure

When starter code is provided:

❌ **Do NOT fork** the assignment repository

❌ **Do NOT submit a forked repository**

Instead, students must:

1. Clone or download the starter repository
2. Create a **new private repository**
3. Copy the starter files into the new repository
4. Commit the code as an initial commit

### Recommended Git workflow

```
git clone https://github.com/<course-org>/<assignment-starter>.git
cd <assignment-starter>
rm -rf .git

git init
git add .
git commit -m "Initial commit from assignment starter code"
git branch -M main
git remote add origin https://github.com/<username>/cse4001-<assignment>-<netid>.git
git push -u origin main
```

------

## 4. Collaborators (required)

Students **must** add the instructor and all TAs as collaborators.

### Required collaborators

- **Instructor**: `eraldoribeiro`
- **Teaching Assistants**:
  - `hatemphd`

> ⚠️ Repositories without correct collaborator access **will not be graded**.

------

## 5. Assignment content requirements

Each repository must include:

- ✅ All required source code
- ✅ Any required screenshots or logs (PNG/JPG/TXT)
- ✅ A completed `README.md` with:
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

## 6. Submitting the assignment

On **Canvas**, students must submit **only** the URL of the repository, e.g.:

```
https://github.com/<username>/cse4001-<assignment-name>-<netid>
```

No additional uploads unless explicitly requested.

------

## 7. Deadlines & late policy

- The **timestamp of the last commit pushed** before the deadline determines submission time
- Late submissions follow the course late policy

------

## 8. Academic integrity

- All submitted work must be **your own**
- Sharing repositories or making them public is prohibited
- Standard university academic integrity policies apply

------

## 9. Common reasons assignments are not graded

- Repository is public
- Instructor or TAs not added as collaborators
- Incorrect repository name
- Forked repository submitted
- No README or missing required files
- Work not pushed before the deadline

------

## 10. Final submission checklist

- [ ]  Repository name is correct
- [ ]  Repository is private
- [ ]  Instructor and TAs added
- [ ]  Code builds and runs
- [ ]  README completed
- [ ]  All changes pushed

------


 
