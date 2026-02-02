---
name: codex
description: Delegate complex math, algorithm, or coding reasoning to OpenAI Codex (GPT-5.2-codex-xhigh). Use for deep reasoning, solving difficult problems, or reviewing plans for blindspots and edge cases.
argument-hint: [task description]
allowed-tools: Bash, Read, Write, Glob, Grep
user-invocable: true
---

# Codex Delegation Skill

Delegate tasks to OpenAI Codex (GPT-5.2-codex-xhigh) which excels at deep reasoning.

## Prerequisites

- OpenAI Codex CLI installed: `npm install -g @openai/codex`
- API key configured for Codex

## When to Use Codex

### Use Case 1: Review Plans for Blindspots and Corner Cases

Before implementing a complex solution, ask Codex to critique your plan:

```bash
codex exec --model gpt-5.2-codex-xhigh --full-auto --output-last-message /tmp/codex-result.md "Review this plan and identify blindspots, corner cases, edge cases, and potential issues:

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

### Use Case 2: Solve Complex Math & Algorithm Problems

For problems requiring deep mathematical or algorithmic reasoning:

```bash
codex exec --model gpt-5.2-codex-xhigh --full-auto --output-last-message /tmp/codex-result.md "Solve this problem: [problem description]. Show your reasoning step by step."
```

### Use Case 3: Implement Difficult Code

For complex implementations you're unsure about:

```bash
codex exec --model gpt-5.2-codex-xhigh --full-auto --output-last-message /tmp/codex-result.md "Implement [description]. Include time/space complexity analysis and handle edge cases."
```

### Use Case 4: Debug Complex Issues

When stuck on a tricky bug:

```bash
codex exec --model gpt-5.2-codex-xhigh --full-auto --output-last-message /tmp/codex-result.md "Debug this code. It should [expected behavior] but instead [actual behavior]:

[code snippet]

Find the root cause and fix."
```

## Execution Steps

### Step 1: Formulate the Task

Write a clear, detailed prompt. Include:
- Specific problem or plan to review
- Relevant context and constraints
- What kind of output you expect

### Step 2: Call Codex

```bash
codex exec --model gpt-5.2-codex-xhigh --full-auto --output-last-message /tmp/codex-result.md "YOUR_TASK"
```

**Flags:**
- `--model gpt-5.2-codex-xhigh` - Highest reasoning capability
- `--full-auto` - Run without interactive prompts
- `--output-last-message /tmp/codex-result.md` - Capture response to file

For file modifications, add `--dangerously-bypass-approvals-and-sandbox` if trusted.

### Step 3: Review Results

```bash
cat /tmp/codex-result.md
```

Also check for file changes:
```bash
git status && git diff
```

### Step 4: Act on Feedback

- For plan reviews: Address the blindspots Codex identified before implementing
- For solutions: Verify correctness, then integrate or iterate

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

- Be specific and detailed - Codex reasons better with full context
- Ask explicitly for edge cases when reviewing plans
- For algorithms, always ask about time/space complexity
- Review Codex's file changes carefully before accepting
- If Codex misses something, iterate with a follow-up prompt
