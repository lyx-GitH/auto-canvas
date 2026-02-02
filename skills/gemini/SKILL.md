---
name: gemini
description: Delegate tasks to Google Gemini API for multimodal reasoning, PDF analysis, and image understanding. Use for summarizing documents, analyzing visuals, or tasks requiring Gemini's multimodal capabilities.
argument-hint: <task description including file paths if needed>
allowed-tools: Bash, Read, Write, Glob, Grep
user-invocable: true
---

# Gemini Delegation Skill

Delegate tasks to Google Gemini API for multimodal reasoning and document analysis.

**Default Model:** `gemini-3-flash-preview` (recommended for best performance)

## Usage

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gemini_api.py" <file_path> "<prompt>" [-m MODEL] [-o OUTPUT]
```

**Arguments:**
- `file_path` - Path to PDF or image file (.pdf, .png, .jpg, .jpeg, .gif, .webp)
- `prompt` - Task or question for Gemini
- `-m, --model` - Model to use (default: `gemini-3-flash-preview`)
- `-o, --output` - Output file path (default: `/tmp/gemini-result.md`)

**Available Models:**
- `gemini-3-flash-preview` - Default, recommended for best quality
- `gemini-2.5-flash` - Faster, good for simple tasks
- `gemini-2.5-pro` - Most capable, for complex analysis

## Examples

### Basic PDF Summary
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gemini_api.py" lecture.pdf "Summarize for exam prep"
```

### With Custom Model
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gemini_api.py" slide.pdf "Extract key concepts" -m gemini-2.5-flash
```

### With Custom Output
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gemini_api.py" diagram.png "Explain this diagram" -o /tmp/diagram-analysis.md
```

### Exam Prep Template
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gemini_api.py" ./slides/lecture5.pdf \
  "Extract exam-relevant content:
- Key Concepts: Core definitions, theorems, techniques
- Formulas: Important equations with explanations
- Exam Focus: Topics likely to appear on exams

Format as markdown. Be comprehensive."
```

## Output

- Result is printed to stdout
- Also saved to output file (default: `/tmp/gemini-result.md`)
- Use the Read tool to retrieve the output file if needed

## Prerequisites

- Python 3.8+
- `google-genai` package: `pip install google-genai python-dotenv`
- API key in `.env` as `GEMINI_API_KEY`

The script searches for `.env` in:
1. Current working directory
2. Plugin root directory
3. Home directory

Or specify custom path in `.canvas-config.json`:
```json
{
  "gemini_env_file": "./path/to/.env"
}
```

## Tips

- Use absolute paths or paths relative to current directory
- For large documents (>10MB), the script auto-uses Files API
- Check stderr for errors if results seem empty
- Use unique output filenames (`-o`) if running multiple queries in parallel
