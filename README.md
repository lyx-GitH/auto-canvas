# Auto Canvas

A Claude Code plugin for automating coursework from Canvas LMS. Syncs slides and assignments, auto-completes homework, and maintains study notes for exam prep.

## Features

- **`/setup`** - Interactive setup wizard (run this first!)
- **`/sync-canvas`** - Fetch new slides and homework from Canvas LMS
- **`/do-my-homework`** - Complete assignments with LaTeX output and study notes
- **`/gemini`** - Delegate PDF/image analysis to Google Gemini
- **`/codex`** - Delegate complex reasoning to OpenAI Codex

## Quick Start

### 1. Install the Plugin

```bash
# From GitHub
claude plugins install github:yourusername/auto-canvas

# Or clone locally
git clone https://github.com/yourusername/auto-canvas.git
claude plugins install ./auto-canvas
```

### 2. Install Dependencies

```bash
pip install google-genai python-dotenv
```

### 3. Create Homework Folder and Run Setup

```bash
mkdir ~/homework
cd ~/homework
claude
> /setup
```

The setup wizard will guide you through:
- Exporting Canvas cookies from your browser
- Entering your Canvas URL
- Fetching your course list automatically
- Selecting which courses to sync
- Creating the folder structure

That's it! After setup, just run `/sync-canvas` to fetch your coursework.

---

## Manual Setup (Alternative)

<details>
<summary>Click to expand manual setup instructions</summary>

### 1. Export Canvas Cookies

1. Log into Canvas in your browser
2. Install the [EditThisCookie](https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg) extension
3. Click the extension icon on Canvas
4. Click "Export" (copies to clipboard)
5. Save to `cookies.json` in your homework folder

### 2. Create Configuration

Create `.canvas-config.json`:

```json
{
  "canvas_base_url": "https://your-school.instructure.com",
  "cookies_file": "./cookies.json",
  "gemini_env_file": "./.env",
  "courses": [
    {
      "id": "123456",
      "folder": "CS101_Intro",
      "name": "Introduction to Computer Science"
    }
  ]
}
```

### 3. Set Up API Keys (Optional)

Create `.env` for Gemini-powered lecture summarization:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. Install Codex CLI (Optional)

```bash
npm install -g @openai/codex
```

</details>

## Usage

### Sync All Courses

```bash
cd ~/homework
claude
> /sync-canvas
```

### Sync Specific Course

```bash
> /sync-canvas CS101
```

### Complete an Assignment

```bash
> /do-my-homework CS101_Intro/hw1/
```

### Analyze a Document with Gemini

```bash
> /gemini analyze slides/lecture5.pdf "Extract key concepts for exam"
```

## Folder Structure

After setup, your homework folder will look like:

```
~/homework/
├── .canvas-config.json     # Canvas configuration
├── cookies.json            # Canvas session (DO NOT COMMIT)
├── .env                    # API keys (DO NOT COMMIT)
├── CLAUDE.md               # Course reference for Claude
├── CS101_Intro/
│   ├── notes.md            # Cumulative study notes
│   ├── syllabus.pdf
│   ├── slides/
│   │   ├── lecture1.pdf
│   │   └── lecture2.pdf
│   └── hw1/
│       ├── description.md
│       ├── solution.tex
│       └── solution.pdf
└── MATH201_Calc/
    └── ...
```

## Configuration Reference

### `.canvas-config.json`

| Field | Description |
|-------|-------------|
| `canvas_base_url` | Your school's Canvas URL (e.g., `https://school.instructure.com`) |
| `cookies_file` | Path to cookies.json (relative to config file) |
| `gemini_env_file` | Path to .env with GEMINI_API_KEY |
| `courses` | Array of course objects |
| `courses[].id` | Canvas course ID (from URL: `/courses/XXXXXX`) |
| `courses[].folder` | Local folder name for this course |
| `courses[].name` | Human-readable course name |

### Finding Canvas Course IDs

1. Go to your course in Canvas
2. Look at the URL: `https://school.instructure.com/courses/123456`
3. The number after `/courses/` is your course ID

## Security Notes

**Never commit these files:**
- `cookies.json` - Contains your Canvas session
- `.env` - Contains API keys
- `.canvas-config.json` - May contain sensitive paths

The `.gitignore` template excludes these automatically.

## Requirements

- Claude Code CLI
- Python 3.8+
- LaTeX distribution (for PDF compilation)
  - macOS: `brew install --cask mactex`
  - Ubuntu: `sudo apt install texlive-full`
- Google Gemini API key (for `/gemini` and lecture summarization)
- OpenAI Codex CLI (optional, for `/codex`)

## How It Works

### `/sync-canvas`

1. Loads configuration from `.canvas-config.json`
2. Authenticates with Canvas using cookies
3. Fetches file/assignment lists via Canvas API
4. Downloads only new content (delta sync)
5. Spawns parallel sub-agents for:
   - Homework completion (`/do-my-homework`)
   - Lecture summarization (`/gemini`)
6. Merges results into `notes.md`

### `/do-my-homework`

1. Parses assignment description (PDF/MD/images)
2. Creates structured workspace
3. Solves problems (uses `/codex` for complex math)
4. Generates concise LaTeX solution
5. Optionally "bakes" key concepts into `notes.md`
6. Compiles to PDF

### Study Notes Philosophy

- `solution.tex` = Concise, submission-ready (derivations + boxed answers)
- `notes.md` = Comprehensive exam prep (explanations, patterns, pitfalls)

This separation keeps submissions clean while building a knowledge base for exams.

## License

MIT
