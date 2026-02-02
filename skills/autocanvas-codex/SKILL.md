---
name: autocanvas-codex
description: Delegate complex math, algorithm, or coding reasoning to the configured reasoning backend (Codex or Claude subagent). Use for deep reasoning, solving difficult problems, or reviewing plans for blindspots and edge cases.
argument-hint: [task description]
allowed-tools: Bash, Read, Write, Glob, Grep, Task
user-invocable: true
---

# Complex Reasoning Skill

Delegate tasks requiring deep reasoning to either OpenAI Codex or a Claude subagent, based on configuration.

## Step 0: Check Reasoning Backend

**First, determine which backend to use from config:**

```bash
# Check config for reasoning backend
if [ -f ".canvas-config.json" ]; then
    BACKEND=$(python3 -c "import json; c=json.load(open('.canvas-config.json')); print(c.get('reasoning_backend', 'claude'))")
    MODEL=$(python3 -c "import json; c=json.load(open('.canvas-config.json')); print(c.get('codex_model', 'gpt-5.2-codex-xhigh'))")
else
    BACKEND="claude"
    MODEL=""
fi
echo "Backend: $BACKEND, Model: $MODEL"
```

**If `reasoning_backend` is `"codex"`:** Use Codex CLI (see Codex Backend section)
**If `reasoning_backend` is `"claude"`:** Use Claude subagent (see Claude Backend section)

---

## Codex Backend

### Prerequisites

- OpenAI Codex CLI installed: `npm install -g @openai/codex`
- API key configured for Codex

### When to Use

1. **Review Plans for Blindspots and Corner Cases**
2. **Solve Complex Math & Algorithm Problems**
3. **Implement Difficult Code**
4. **Debug Complex Issues**

### Execution

```bash
# Get model from config (default: gpt-5.2-codex-xhigh)
MODEL=$(python3 -c "import json; c=json.load(open('.canvas-config.json')); print(c.get('codex_model', 'gpt-5.2-codex-xhigh'))")

codex exec --model "$MODEL" --full-auto --output-last-message /tmp/codex-result.md "YOUR_TASK"
```

**Flags:**
- `--model` - Model from config (default: `gpt-5.2-codex-xhigh`)
- `--full-auto` - Run without interactive prompts
- `--output-last-message /tmp/codex-result.md` - Capture response to file

For file modifications, add `--dangerously-bypass-approvals-and-sandbox` if trusted.

### Example: Plan Review

```bash
MODEL=$(python3 -c "import json; c=json.load(open('.canvas-config.json')); print(c.get('codex_model', 'gpt-5.2-codex-xhigh'))")

codex exec --model "$MODEL" --full-auto --output-last-message /tmp/codex-result.md "Review this plan and identify blindspots, corner cases, edge cases, and potential issues:

PLAN:
[Your plan here]

CONTEXT:
[Relevant background]

Please analyze:
1. What edge cases or corner cases might break this approach?
2. What blindspots or assumptions am I missing?
3. What failure modes should I handle?
4. Are there race conditions, overflow issues, or boundary problems?
5. What improvements would make this more robust?"
```

### Reading Results

```bash
cat /tmp/codex-result.md
```

---

## Claude Backend

When Codex is not configured or not installed, use a Claude subagent for complex reasoning.

### Execution

Use the Task tool to spawn a reasoning subagent:

```python
# Task tool parameters
subagent_type: "general-purpose"
model: "opus"  # Use strongest model for complex reasoning
description: "Complex reasoning task"
prompt: """
You are a expert mathematician and algorithm specialist. Solve the following problem with rigorous step-by-step reasoning.

TASK:
{task_description}

REQUIREMENTS:
1. Show all steps clearly
2. Identify edge cases and corner cases
3. Verify your solution
4. Provide complexity analysis if applicable

Be thorough and precise.
"""
```

### Example: Plan Review with Claude

```python
# Task tool parameters
subagent_type: "general-purpose"
model: "opus"
description: "Review plan for blindspots"
prompt: """
You are a senior software architect reviewing a technical plan. Identify blindspots, corner cases, and potential issues.

PLAN:
{plan_description}

CONTEXT:
{relevant_background}

ANALYZE:
1. What edge cases or corner cases might break this approach?
2. What blindspots or assumptions are being made?
3. What failure modes should be handled?
4. Are there race conditions, overflow issues, or boundary problems?
5. What improvements would make this more robust?

Be thorough and critical.
"""
```

### Example: Solve Math Problem with Claude

```python
# Task tool parameters
subagent_type: "general-purpose"
model: "opus"
description: "Solve complex math problem"
prompt: """
You are an expert mathematician. Solve this problem with rigorous proof.

PROBLEM:
{problem_statement}

REQUIREMENTS:
1. Show complete step-by-step derivation
2. State any assumptions clearly
3. Check edge cases (n=0, n=1, negative, infinity)
4. Box the final answer
5. Verify the solution by substitution if possible

Be precise and thorough.
"""
```

---

## Task Templates

### Plan Review Template
```
Review this plan and identify blindspots, corner cases, and potential issues:

PLAN:
[Describe your approach]

CONTEXT:
- Problem: [what you're solving]
- Constraints: [time, space, requirements]
- Assumptions: [what you're assuming]

ANALYZE:
1. Edge cases that could break this?
2. Blindspots or missing considerations?
3. Failure modes to handle?
4. Off-by-one, overflow, or boundary issues?
5. Concurrency or race conditions?
6. Suggested improvements?
```

### Problem Solving Template
```
TASK: [Brief description]

PROBLEM:
[Full problem statement]

CONSTRAINTS:
- [Time/space limits]
- [Input bounds]

REQUIREMENTS:
1. [What the solution must do]
2. [Edge cases to handle]

Provide solution with complexity analysis.
```

## Tips

- Be specific and detailed - both backends reason better with full context
- Ask explicitly for edge cases when reviewing plans
- For algorithms, always ask about time/space complexity
- Review results carefully before accepting
- If the result misses something, iterate with a follow-up prompt
