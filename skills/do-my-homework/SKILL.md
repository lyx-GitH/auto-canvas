---
name: do-my-homework
description: Complete coursework assignments and coding projects. Extracts info, sets up workspace, solves problems (using /codex for complex tasks), reflects/tests, bakes notes for exam prep, and polishes output to PDF.
argument-hint: <path-to-homework-file-or-project-folder>
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebFetch, AskUserQuestion, Skill
user-invocable: true
---

# Do My Homework Skill

Complete coursework assignments and coding projects following a structured procedure.

## Usage

```
/do-my-homework <path-to-file-or-folder>
```

## Procedure

Execute these steps in order:

### Step 1: Input Processing

- Accept the provided file path or folder path as input argument
- If no path provided, use AskUserQuestion to request:
  - The homework description file OR project folder path
- Supported inputs:
  - Single file (PDF, DOCX, TXT, MD, images) for homework descriptions
  - Folder containing project requirements and optionally code skeleton
- Read the input file(s) to understand the assignment

### Step 2: Extract Information

Analyze the input and extract:
- **Course name** (e.g., "HPC", "DataVis", "CS101", "Math201")
- **Assignment name** (e.g., "hw1", "proj2", "midterm", "lab3")
- **Assignment type**: "homework" (written/math) or "project" (coding)

Present extracted info and ask user with AskUserQuestion:
1. Confirm/correct course name and assignment name
2. "Would you like to 'bake into notes' after completion?" (Explain: summarizes key concepts to `{course}/notes.md` for exam prep)

Store user's bake preference for Step 6.

### Step 3: Setup Working Directory

Set `hw_pwd` = current working directory + `{course_name}/{hw_name}/`

```bash
mkdir -p {course_name}/{hw_name}
```

**For written homework:**
- Convert input to `{hw_pwd}/description.md`
- If PDF: use Gemini to extract text preserving structure
  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gemini_api.py" "{input_pdf}" \
    "Extract all text from this document. Preserve structure, equations, and formatting. Output as markdown." \
    -o "{hw_pwd}/description.md"
  ```
- If DOCX: convert to markdown
- If image: describe the problems visible
- Preserve all problem statements, equations, figures, requirements

**For coding projects:**
- Create `{hw_pwd}/description.md` with requirements
- Check if input contains code skeleton/starter files
- If NO skeleton found, ask user via AskUserQuestion:
  - Option A: "Provide path to code skeleton"
  - Option B: "Construct project from scratch"
- If skeleton provided, copy to `{hw_pwd}/` preserving structure

### Step 4: Solve

**For written homework:**
Create `{hw_pwd}/solution.tex` with proper LaTeX:

```latex
\documentclass[11pt]{article}
\usepackage[utf8]{inputenc}
\usepackage{amsmath,amssymb,amsthm}
\usepackage[margin=1in]{geometry}

\title{[Course] -- [Assignment Name]}
\author{}
\date{}

\begin{document}
\maketitle

\section*{Problem 1}
% Concise solution

\end{document}
```

**CRITICAL: Keep solution.tex CONCISE and CLEAN:**
- Focus on mathematical derivations and boxed answers
- NO verbose explanations like "Efficiency measures how well we utilize..."
- NO trivial background knowledge or definitions
- NO unnecessary commentary or hand-holding prose
- Just: Given -> Derivation -> Boxed Answer
- Brief justifications only where mathematically necessary
- All background knowledge, explanations, tricks go to notes.md instead

**For complex math/algorithms/proofs**: Call `/codex` skill

**For coding projects:**
- Implement required functionality in `{hw_pwd}/`
- Follow language best practices and style guides
- Add comments explaining non-obvious logic only
- **For complex algorithms or stuck debugging**: Call `/codex` skill
- Create any required configuration files

### Step 5: Reflect and Verify

**For written homework:**
- Review each solution step-by-step
- Verify calculations and logic
- Check edge cases (n=0, n=1, negative, infinity)
- Use `/codex` to double-check complex proofs if uncertain
- If errors found: fix in solution.tex, repeat verification

**For coding projects:**
- Run provided test cases
- If no tests provided, create basic tests
- Test edge cases and error handling
- If tests fail: debug (use `/codex` if stuck), fix code, retest
- Repeat until all tests pass

### Step 6: Bake into Notes

**Only if user agreed in Step 2.**

Create or append to `{course_name}/notes.md`:

```markdown
---
## [Assignment Name] Key Concepts
*Added: [date]*

### Core Definitions
- [Define key terms - this is where definitions belong, NOT in solution.tex]

### Formulas & Theorems
- [Key equations to memorize]
- [Important theorems used]

### Problem-Solving Patterns
- [Techniques and tricks used]
- [When to apply each method]

### Common Pitfalls
- [Mistakes to avoid]
- [Edge cases to remember]

### Exam Focus
- [Types of questions likely on exam]
- [What to practice]

---
```

**Important**:
- Assume user does NOT attend lectures
- Extract ALL teachable content - homework is their primary learning source
- This is where verbose explanations and background knowledge belong

### Step 7: Polish and Handover

**Polish solution.tex:**
- Ensure conciseness - remove any verbose explanations that crept in
- Keep only essential mathematical prose
- Maintain academic tone without being wordy

**Compile to PDF:**
```bash
cd {hw_pwd}
pdflatex -interaction=nonstopmode solution.tex
pdflatex -interaction=nonstopmode solution.tex  # Run twice for refs
```

If compilation errors: fix LaTeX issues and retry.

**For coding projects with report requirement:**
- Create `{hw_pwd}/report.tex` - keep concise unless instructions specify otherwise
- Include code snippets, results, analysis
- Compile: `pdflatex report.tex`

**Final handover - report to user:**
- List all created/modified files
- Path to final PDF: `{hw_pwd}/solution.pdf`
- Summary of what was completed
- If bake was done: mention notes.md was updated

## Style Guide for solution.tex

**DO:**
```latex
\subsection*{(a)}
\[
S(p) = \frac{T_s}{T_p} = \frac{4n}{\frac{8n}{p} + 1000 \log p}
\]
For $n \gg p$, the term $\frac{8n}{p}$ dominates:
\[
\boxed{S_{\max}(p) = \frac{p}{2}}
\]
```

**DON'T:**
```latex
\subsection*{(a)}
Recall that speedup is defined as the ratio of serial runtime to parallel runtime,
which measures how much faster we can solve a problem using multiple processors.
The speedup is given by:
\[
S(p) = \frac{T_s}{T_p}
\]
Now, let's substitute our given values...
```

## Important Notes

- All work stored in `{course_name}/{hw_name}/`
- Use `/codex` for complex proofs, algorithms, debugging
- solution.tex = concise derivations + boxed answers
- notes.md = explanations, background, exam prep
- Keep notes.md cumulative across assignments
