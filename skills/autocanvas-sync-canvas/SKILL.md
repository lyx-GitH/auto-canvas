---
name: autocanvas-sync-canvas
description: Sync coursework from Canvas LMS. Fetches new slides and homework, then COMPLETES all new assignments by calling /autocanvas-do-my-homework for each one. Also summarizes lectures and updates study notes. Use when asked to "sync canvas", "check for new homework", "update courses", or "fetch slides". IMPORTANT - This skill MUST call /autocanvas-do-my-homework to solve homework, not just download it.
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

### Step 5: Spawn Sub-Agents and Continue Working (Non-Blocking)

**CRITICAL: DO NOT WAIT for sub-agents. Launch them in background and IMMEDIATELY continue to the next task.**

#### Architecture

```
Master Agent (this skill)
    |
    |-- [BACKGROUND] Spawn Lecture Summarization sub-agents
    |       (run_in_background: true, DO NOT WAIT)
    |
    |-- [FOREGROUND] Continue to Step 5.2: Complete homework assignments
    |       (Master does this work directly, or spawns homework agents)
    |
    |-- [FINALLY] Step 6: Check sub-agent completion and merge notes
```

**Key principle:** Lecture summarization is I/O-bound (reading PDFs, calling APIs). Homework completion requires reasoning. Run summarization in background while master focuses on homework.

#### 5.1: Spawn Lecture Summarization Sub-Agents (BACKGROUND - DO NOT WAIT)

**First, check the summarization backend from config.**

Spawn summarization agents with `run_in_background: true`. **Do NOT use TaskOutput to wait for them yet.** Immediately proceed to Step 5.2 after spawning.

#### 5.2: Complete Homework Assignments (FOREGROUND - MANDATORY)

**CRITICAL: After spawning summarization agents, you MUST complete the homework assignments.**

**This is the main purpose of /autocanvas-sync-canvas - do not skip this step!**

For EACH new assignment found in Step 4:

1. **Use the Skill tool to invoke `/autocanvas-do-my-homework`:**
   ```python
   # Use Skill tool with these parameters:
   skill: "autocanvas-do-my-homework"
   args: "{homework_path}"
   ```

2. **Example:** If you found new homework at `CS101_Intro/hw2/`:
   ```
   Invoke Skill tool:
     skill: "autocanvas-do-my-homework"
     args: "CS101_Intro/hw2/"
   ```

3. **Repeat for each new assignment** - do not stop after one.

**DO NOT:**
- Skip homework completion
- Only download files without solving
- Wait for summarization before starting homework
- Forget to call /autocanvas-do-my-homework

**The homework MUST be solved. This is not optional.**

#### 5.3: Summarization Sub-Agent Details

**Spawn these FIRST (before homework), then move on without waiting:**

```python
# Task tool parameters
subagent_type: "general-purpose"
run_in_background: true  # CRITICAL: must be true
description: "Summarize lectures for {course}"
prompt: """
Summarize new lecture slides for {course} and write to /tmp/lecture-notes-{course}.md

Slides to process:
{list of new slide paths}

Write output ONLY to /tmp/lecture-notes-{course}.md (not to notes.md directly).
"""
```

**After spawning, DO NOT call TaskOutput. Proceed immediately to homework.**

#### Summarization Prompt Templates (for Step 5.3)

**If using Gemini backend:**
```
Summarize new lecture slides for {course}.
Use: python3 ~/.claude/skills/scripts/gemini_api.py "{slide}" "Extract exam-relevant content..." -o /tmp/summary-{slide}.md
Write final output to /tmp/lecture-notes-{course}.md
```

**If using Claude backend:**
```
Read PDFs directly with Read tool. Extract key concepts, formulas, exam focus.
Write output to /tmp/lecture-notes-{course}.md
```

---

### Step 6: After Homework Done, Check Sub-Agents and Merge Notes

**Only after completing all homework in Step 5.2**, check if background summarization agents are done:

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
