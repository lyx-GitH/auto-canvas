---
name: autocanvas-sync-canvas
description: Sync coursework from Canvas LMS. Fetches new slides and homework, places them correctly, auto-completes eligible assignments, and updates study notes. Use when asked to "sync canvas", "check for new homework", "update courses", or "fetch slides".
argument-hint: [course-name] (optional, syncs all courses if omitted)
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebFetch, Task, Skill
user-invocable: true
---

# Sync Canvas Skill

Synchronize coursework from Canvas LMS. Fetches new slides/homework, auto-completes eligible assignments, and updates study notes.

## Step 0: Check Setup (REQUIRED FIRST)

**Before doing anything else, verify that auto-canvas is set up.**

```bash
# Check if config exists
if [ ! -f ".canvas-config.json" ]; then
    echo "NOT_SETUP"
else
    echo "SETUP_OK"
fi
```

**If NOT_SETUP:**

Use AskUserQuestion to ask the user:
- Question: "Auto-canvas is not set up yet. Would you like to run setup now?"
- Header: "Setup"
- Options:
  - "Yes, run /autocanvas-setup now"
  - "No, I'll set it up manually later"

If user selects "Yes", invoke the `/autocanvas-setup` skill using the Skill tool and STOP this skill.
If user selects "No", display instructions and STOP:

```
To set up manually, you need:
1. .canvas-config.json - Copy from plugin templates/config.example.json
2. cookies.json - Export from your browser's Canvas session
3. .env - Add your GEMINI_API_KEY

Or run /autocanvas-setup anytime to use the interactive wizard.
```

**Only proceed to Step 1 if setup is complete.**

---

## Prerequisites (verified by setup)

- `.canvas-config.json` in current directory
- `cookies.json` with valid Canvas session cookies
- `.env` with `GEMINI_API_KEY` (for lecture summarization)

## Configuration Loading

**CRITICAL: Always load config first before any Canvas operations.**

```bash
# Validate config exists and is valid
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/load_config.py" --validate

# Load configuration values
CANVAS_URL=$(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/load_config.py" --canvas-url)
COOKIES_FILE=$(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/load_config.py" --cookies-file)
COURSES_JSON=$(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/load_config.py" --courses)
```

## Process

### Step 1: Validate Canvas Access

```bash
# Build cookie string from cookies.json
COOKIE_STR=$(python3 -c "
import json
cookies = json.load(open('$COOKIES_FILE'))
print('; '.join(f\"{c['name']}={c['value']}\" for c in cookies if 'instructure' in c.get('domain','')))
")

# Test API access
curl -s -b "$COOKIE_STR" "${CANVAS_URL}/api/v1/users/self" | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('name','INVALID'))"
```

**If INVALID:** Stop and ask user to refresh cookies.

### Step 2: Check for New Content

For each course in config:
1. List Canvas files and assignments via API
2. Compare with local `slides/` and `hw*/` folders
3. Identify deltas (new files not yet downloaded)

```bash
# Example: List course files
COURSE_ID="123456"
curl -s -b "$COOKIE_STR" "${CANVAS_URL}/api/v1/courses/${COURSE_ID}/files?per_page=100"
```

### Step 3: Fetch New Slides (Delta Only)

Download new slides to `{course_folder}/slides/`

### Step 4: Fetch New Homework (Delta Only)

Create `hw{N}/` folder and download description + attachments.

### Step 5: Spawn Sub-Agents (Parallel, Isolated)

**IMPORTANT: Use sub-agents to avoid context pollution and prevent file conflicts.**

#### Architecture

```
Master Agent (this skill)
    |
    +-> Sub-Agent A: Homework Completion
    |   +-> writes to: /tmp/hw-notes-{course}.md
    |
    +-> Sub-Agent B: Lecture Summarization
    |   +-> writes to: /tmp/lecture-notes-{course}.md
    |
    +-> After BOTH complete:
        +-> Master merges into: {course_folder}/notes.md
```

#### 5.1: Spawn Homework Sub-Agent (if new assignments)

```python
# Task tool parameters
subagent_type: "general-purpose"
run_in_background: true
description: "Complete homework for {course}"
prompt: """
Complete the homework at {homework_path}

IMPORTANT: When baking notes, write to /tmp/hw-notes-{course}.md instead of notes.md directly.
This avoids conflicts with parallel lecture summarization.

Follow /autocanvas-do-my-homework procedure but output notes to the temp file.
"""
```

#### 5.2: Spawn Lecture Summarization Sub-Agent (if new slides)

**First, check the summarization backend from config:**

```bash
SUMM_BACKEND=$(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/load_config.py" --summarization-backend)
```

**If using Gemini backend:**

```python
# Task tool parameters
subagent_type: "general-purpose"
run_in_background: true
description: "Summarize lectures for {course}"
prompt: """
Summarize new lecture slides for {course} and write to /tmp/lecture-notes-{course}.md

Slides to process:
{list of new slide paths}

For EACH slide not already in notes:
1. Run gemini_api.py to summarize:
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gemini_api.py" "{slide}" \
     "Extract exam-relevant content:
     - Key Concepts: Core definitions, theorems, techniques
     - Formulas: Important equations with explanations
     - Exam Focus: Topics likely to appear on exams
     Format as markdown." \
     -o /tmp/summary-{slide_name}.md

2. Read the summary and append to /tmp/lecture-notes-{course}.md

Process multiple slides in parallel using background bash commands.
"""
```

**If using Claude backend:**

```python
# Task tool parameters
subagent_type: "general-purpose"
run_in_background: true
model: "sonnet"
description: "Summarize lectures for {course}"
prompt: """
Summarize new lecture slides for {course} and write to /tmp/lecture-notes-{course}.md

Slides to process:
{list of new slide paths}

For EACH slide not already in notes:
1. Read the PDF file directly using the Read tool
2. Extract exam-relevant content:
   - Key Concepts: Core definitions, theorems, techniques
   - Formulas: Important equations with explanations
   - Exam Focus: Topics likely to appear on exams
3. Append the summary to /tmp/lecture-notes-{course}.md with format:
   ---
   ## Lecture: {slide_name}
   *Added: {date}*

   {summary content}

   ---

Process slides sequentially to avoid conflicts.
"""
```

### Step 6: Wait and Merge Notes

After spawning sub-agents, wait for completion, then merge:

```bash
# Wait for sub-agents to complete (check task status)

# Merge temp files into notes.md for each course
COURSE_FOLDERS=$(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/load_config.py" --course-folders)

for course in $COURSE_FOLDERS; do
    notes_file="${course}/notes.md"

    # Append homework notes if exists
    if [ -f "/tmp/hw-notes-${course}.md" ]; then
        cat "/tmp/hw-notes-${course}.md" >> "$notes_file"
        rm "/tmp/hw-notes-${course}.md"
    fi

    # Append lecture notes if exists
    if [ -f "/tmp/lecture-notes-${course}.md" ]; then
        cat "/tmp/lecture-notes-${course}.md" >> "$notes_file"
        rm "/tmp/lecture-notes-${course}.md"
    fi
done
```

### Step 7: Generate Report

```
## Canvas Sync Report - {date}

### New Slides Downloaded
- {course}: {list or "none"}
- ...

### New Assignments
- {course}: hw{N} - {status}

### Notes Updated
- {courses where notes.md was updated}

### Action Required
- {items needing attention}
```

## Key Design Principles

1. **Config-driven** - All paths and settings from `.canvas-config.json`
2. **Delta sync only** - Never re-download existing files
3. **Sub-agent isolation** - Heavy work in sub-agents, not main context
4. **No file conflicts** - Sub-agents write to separate temp files
5. **Master merges** - Only master agent writes to final notes.md
6. **Parallel by course** - Different courses can run fully in parallel
