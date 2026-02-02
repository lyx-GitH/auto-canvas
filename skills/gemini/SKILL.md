---
name: gemini
description: Delegate tasks to the configured summarization backend (Gemini or Claude) for PDF analysis, image understanding, and document summarization. Use for summarizing lectures, analyzing diagrams, or extracting content from documents.
argument-hint: <file_path> "<prompt>"
allowed-tools: Bash, Read, Write, Glob, Grep, Task
user-invocable: true
---

# Document Analysis Skill

Delegate PDF/image analysis to either Google Gemini or a Claude subagent, based on configuration.

## Step 0: Check Summarization Backend

**First, determine which backend to use from config:**

```bash
# Check config for summarization backend
if [ -f ".canvas-config.json" ]; then
    BACKEND=$(python3 -c "import json; c=json.load(open('.canvas-config.json')); print(c.get('summarization_backend', 'claude'))")
    MODEL=$(python3 -c "import json; c=json.load(open('.canvas-config.json')); print(c.get('gemini_model', 'gemini-3-flash-preview'))")
else
    BACKEND="claude"
    MODEL=""
fi
echo "Backend: $BACKEND, Model: $MODEL"
```

**If `summarization_backend` is `"gemini"`:** Use Gemini API (see Gemini Backend section)
**If `summarization_backend` is `"claude"`:** Use Claude subagent (see Claude Backend section)

---

## Gemini Backend

### Prerequisites

- Python 3.8+
- `google-genai` package: `pip install google-genai python-dotenv`
- API key in `.env` as `GEMINI_API_KEY`

### Usage

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gemini_api.py" <file_path> "<prompt>" [-m MODEL] [-o OUTPUT]
```

**Arguments:**
- `file_path` - Path to PDF or image file (.pdf, .png, .jpg, .jpeg, .gif, .webp)
- `prompt` - Task or question for Gemini
- `-m, --model` - Model to use (default from config: `gemini-3-flash-preview`)
- `-o, --output` - Output file path (default: `/tmp/gemini-result.md`)

### Examples

**Basic PDF Summary:**
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gemini_api.py" lecture.pdf "Summarize for exam prep"
```

**Exam Prep Template:**
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gemini_api.py" ./slides/lecture5.pdf \
  "Extract exam-relevant content:
- Key Concepts: Core definitions, theorems, techniques
- Formulas: Important equations with explanations
- Exam Focus: Topics likely to appear on exams

Format as markdown. Be comprehensive."
```

### Output

- Result is printed to stdout
- Also saved to output file (default: `/tmp/gemini-result.md`)
- Use the Read tool to retrieve the output file if needed

---

## Claude Backend

When Gemini is not configured, use a Claude subagent for document analysis.

### Execution

Use the Task tool to spawn an analysis subagent:

```python
# Task tool parameters
subagent_type: "general-purpose"
model: "sonnet"  # Good balance of speed and quality for summarization
description: "Analyze document: {filename}"
prompt: """
Analyze the following document and respond to the user's request.

FILE: {file_path}
(Read this file using the Read tool - Claude can read PDFs directly)

USER REQUEST:
{prompt}

Provide a thorough, well-structured response.
"""
```

### Example: Lecture Summary with Claude

```python
# Task tool parameters
subagent_type: "general-purpose"
model: "sonnet"
description: "Summarize lecture PDF"
prompt: """
Read and analyze the lecture slides at: {file_path}

Extract exam-relevant content:
- Key Concepts: Core definitions, theorems, techniques
- Formulas: Important equations with explanations
- Exam Focus: Topics likely to appear on exams

Format as markdown. Be comprehensive.
"""
```

### Example: Diagram Analysis with Claude

```python
# Task tool parameters
subagent_type: "general-purpose"
model: "sonnet"
description: "Analyze diagram"
prompt: """
Read and analyze the image at: {file_path}

Explain:
1. What the diagram represents
2. Key components and their relationships
3. Important concepts illustrated

Be detailed and clear.
"""
```

---

## Task Templates

### Exam Prep Template
```
Extract exam-relevant content from this document:

- Key Concepts: Core definitions, theorems, techniques
- Formulas: Important equations with explanations
- Exam Focus: Topics likely to appear on exams
- Practice Problems: Example questions based on the material

Format as markdown.
```

### Quick Summary Template
```
Provide a concise summary of this document:

1. Main topics covered
2. Key takeaways
3. Important terms defined

Keep it brief but comprehensive.
```

### Diagram Analysis Template
```
Analyze this diagram/figure:

1. What does it represent?
2. Key components and labels
3. Relationships between elements
4. Concepts being illustrated
```

## Tips

- For PDFs with complex diagrams, Gemini often provides better visual analysis
- Claude can read PDFs directly but processes them as text
- Use specific prompts for better results
- For large documents, consider processing page by page
