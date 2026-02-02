---
name: setup
description: Set up auto-canvas for first-time use. Creates config file, fetches course list from Canvas, and builds folder structure. Use when asked to "setup canvas", "initialize homework folder", or "configure auto-canvas".
argument-hint: (no arguments needed)
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebFetch, AskUserQuestion
user-invocable: true
---

# Auto-Canvas Setup Skill

Interactive setup wizard for first-time auto-canvas configuration.

## Process

### Step 1: Welcome and Cookies Guide

Display to user:

```
## Auto-Canvas Setup

Welcome! Let's set up your homework folder.

### Step 1: Get Canvas Cookies

You need to export your Canvas session cookies:

1. **Log into Canvas** in your browser (Chrome/Edge/Firefox)

2. **Install a cookie export extension:**
   - Chrome/Edge: [EditThisCookie](https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg)
   - Firefox: [Cookie Quick Manager](https://addons.mozilla.org/en-US/firefox/addon/cookie-quick-manager/)

3. **Export cookies:**
   - Go to your Canvas page (e.g., https://school.instructure.com)
   - Click the extension icon
   - Click "Export" (copies JSON to clipboard)

4. **Save to file:**
   - Create a file called `cookies.json` in this folder
   - Paste the exported content and save

Once you've saved cookies.json, let me know!
```

Use AskUserQuestion:
- Question: "Have you saved your Canvas cookies to cookies.json?"
- Options:
  - "Yes, cookies.json is ready"
  - "I need help with this step"

If user needs help, provide more detailed guidance. Wait until cookies.json exists.

### Step 2: Verify cookies.json Exists

```bash
if [ -f "cookies.json" ]; then
    echo "Found cookies.json"
else
    echo "cookies.json not found in current directory"
    exit 1
fi
```

### Step 3: Get Canvas Base URL

Use AskUserQuestion:
- Question: "What is your Canvas base URL?"
- Header: "Canvas URL"
- Options:
  - "https://canvas.instructure.com (Generic Canvas)"
  - "Other (I'll type my school's URL)"

If user selects "Other", they can type their URL.

Validate the URL format (should be https and contain instructure.com or be a valid Canvas instance).

### Step 4: Test Canvas Connection

```bash
# Build cookie string
CANVAS_URL="{user_provided_url}"
COOKIE_STR=$(python3 -c "
import json
cookies = json.load(open('cookies.json'))
print('; '.join(f\"{c['name']}={c['value']}\" for c in cookies if 'instructure' in c.get('domain','').lower() or '{domain}' in c.get('domain','').lower()))
")

# Test API
RESULT=$(curl -s -b "$COOKIE_STR" "${CANVAS_URL}/api/v1/users/self")
USER_NAME=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('name',''))" 2>/dev/null)

if [ -z "$USER_NAME" ]; then
    echo "ERROR: Could not authenticate with Canvas"
    echo "Response: $RESULT"
    exit 1
else
    echo "Authenticated as: $USER_NAME"
fi
```

If authentication fails, inform user their cookies may be expired and they need to re-export.

### Step 5: Fetch Course List

```bash
# Fetch active courses
COURSES=$(curl -s -b "$COOKIE_STR" "${CANVAS_URL}/api/v1/courses?enrollment_state=active&per_page=50")

# Parse and display
python3 << 'EOF'
import json
import sys

courses_json = '''COURSES_PLACEHOLDER'''
courses = json.loads(courses_json)

print("\n## Your Canvas Courses\n")
print("| # | Course Name | Course ID |")
print("|---|-------------|-----------|")

for i, course in enumerate(courses, 1):
    name = course.get('name', 'Unknown')[:40]
    course_id = course.get('id', 'N/A')
    print(f"| {i} | {name} | {course_id} |")
EOF
```

### Step 6: Select Courses to Sync

Use AskUserQuestion with multiSelect:
- Question: "Which courses do you want to sync? (select all that apply)"
- Options: List course names from API response (up to 4, or paginate)

For each selected course, ask for folder name:
- Suggest format: `{DEPT}{NUM}_{ShortName}` (e.g., `CS101_Intro`)
- User can accept suggestion or provide custom name

### Step 7: Document Analysis Backend (Gemini vs Claude)

Use AskUserQuestion:
- Question: "For PDF/lecture summarization, do you want to use Google Gemini or Claude?"
- Header: "Summarization"
- Options:
  - "Google Gemini (requires API key, better for PDFs)"
  - "Claude subagent (no extra setup needed)"

**If user selects Gemini:**

- Ask user to provide their GEMINI_API_KEY
- Create `.env` file with the key
- Set config values:
  - `summarization_backend`: `"gemini"`
  - `gemini_model`: `"gemini-3-flash-preview"` (default, or let user choose)

**If user selects Claude:**

- Set config values:
  - `summarization_backend`: `"claude"`
  - `gemini_model`: `null`

**Note:** Claude can read PDFs directly but Gemini may provide better multimodal analysis for complex diagrams.

### Step 8: Complex Reasoning Backend (Codex vs Claude)

Use AskUserQuestion:
- Question: "For complex math/algorithm reasoning, do you want to use OpenAI Codex or Claude?"
- Header: "Reasoning"
- Options:
  - "OpenAI Codex (requires separate installation)"
  - "Claude subagent (no extra setup needed)"

**If user selects Codex:**

Check if codex is installed:
```bash
if command -v codex &> /dev/null; then
    echo "CODEX_INSTALLED"
else
    echo "CODEX_NOT_INSTALLED"
fi
```

If not installed, use AskUserQuestion:
- Question: "Codex CLI is not installed. Would you like to install it now?"
- Options:
  - "Yes, install codex (requires npm)"
  - "No, use Claude subagent instead"

If user wants to install:
```bash
npm install -g @openai/codex
```

After installation (or if already installed), ask for model preference:
- Question: "Which Codex model do you want to use for complex reasoning?"
- Header: "Codex Model"
- Options:
  - "gpt-5.2-codex-xhigh (Recommended, best reasoning)"
  - "gpt-5.2-codex-high (Good balance)"
  - "Other (I'll type the model name)"

Save the selection. Set config values:
- `reasoning_backend`: `"codex"`
- `codex_model`: `"{selected_model}"` (default: `"gpt-5.2-codex-xhigh"`)

**If user selects Claude (or falls back to Claude):**

Set config values:
- `reasoning_backend`: `"claude"`
- `codex_model`: `null`

### Step 9: Create Configuration

**Note:** Step numbers 9-11 shifted from original 8-10.

Write `.canvas-config.json`:

```python
import json

config = {
    "canvas_base_url": "{CANVAS_URL}",
    "cookies_file": "./cookies.json",
    "gemini_env_file": "./.env",
    "summarization_backend": "gemini",  # or "claude"
    "gemini_model": "gemini-3-flash-preview",  # null if using claude
    "reasoning_backend": "codex",  # or "claude"
    "codex_model": "gpt-5.2-codex-xhigh",  # null if using claude
    "courses": [
        {
            "id": "{course_id}",
            "folder": "{folder_name}",
            "name": "{course_name}"
        }
        # ... for each selected course
    ]
}

with open('.canvas-config.json', 'w') as f:
    json.dump(config, f, indent=2)
```

### Step 9: Create Folder Structure

```bash
# For each course in config
for course_folder in {list_of_folders}; do
    mkdir -p "${course_folder}/slides"

    # Create empty notes.md
    if [ ! -f "${course_folder}/notes.md" ]; then
        echo "# ${course_name} - Study Notes" > "${course_folder}/notes.md"
        echo "" >> "${course_folder}/notes.md"
        echo "Cumulative notes for exam preparation." >> "${course_folder}/notes.md"
        echo "" >> "${course_folder}/notes.md"
    fi
done
```

### Step 10: Create CLAUDE.md

Generate `CLAUDE.md` from config:

```markdown
# Homework Folder

This folder contains coursework and assignments.

## Configuration

- Canvas config: `.canvas-config.json`
- Canvas cookies: `cookies.json` (do not commit)
- API keys: `.env` (do not commit)

## Courses

| Folder | Course | Canvas ID |
|--------|--------|-----------|
{generate_from_config}

## Folder Structure

Each course folder follows this schema:
```
<course_folder>/
├── notes.md          # Exam prep notes (cumulative)
├── syllabus.pdf      # Course syllabus
├── slides/           # Lecture slides
└── hw<N>/            # Homework folders
    ├── description.md
    ├── solution.tex
    └── solution.pdf
```

## Skills

- `/sync-canvas` - Fetch new slides/homework from Canvas
- `/do-my-homework <path>` - Complete a specific assignment
```

### Step 11: Final Summary

Display to user:

```
## Setup Complete!

### Created Files:
- .canvas-config.json (Canvas configuration)
- .env (API keys) [if Gemini was configured]
- CLAUDE.md (project reference)

### Created Folders:
{list_folders_created}

### Next Steps:

1. **Sync your courses:**
   ```
   /sync-canvas
   ```

2. **Complete an assignment:**
   ```
   /do-my-homework {first_course}/hw1/
   ```

### Important:
- Re-export cookies.json if Canvas session expires
- Never commit cookies.json or .env to git
```

## Error Handling

### Invalid Cookies
If Canvas returns 401 or empty user:
```
Your Canvas session appears to be expired or invalid.

Please:
1. Log into Canvas in your browser
2. Re-export cookies using the extension
3. Save to cookies.json
4. Run /setup again
```

### No Courses Found
If course list is empty:
```
No active courses found. This could mean:
1. You're not enrolled in any courses this term
2. The cookies don't have the right permissions
3. The Canvas URL might be incorrect

Please verify your Canvas URL and try again.
```

### Network Errors
If curl fails:
```
Could not connect to Canvas. Please check:
1. Your internet connection
2. The Canvas URL is correct
3. Canvas is not under maintenance
```
