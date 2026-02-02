#!/usr/bin/env python3
"""
Load and validate canvas configuration.

Usage:
    python3 load_config.py                        # Print full config as JSON
    python3 load_config.py --canvas-url           # Print Canvas base URL
    python3 load_config.py --cookies-file         # Print cookies file path
    python3 load_config.py --courses              # Print courses as JSON array
    python3 load_config.py --course-folders       # Print space-separated folder names
    python3 load_config.py --summarization-backend # Print summarization backend (gemini or claude)
    python3 load_config.py --gemini-model         # Print gemini model name
    python3 load_config.py --reasoning-backend    # Print reasoning backend (codex or claude)
    python3 load_config.py --codex-model          # Print codex model name
"""

import argparse
import json
import sys
from pathlib import Path


def find_config():
    """Find .canvas-config.json in current directory or parents."""
    current = Path.cwd()

    # Check current and parent directories
    for _ in range(5):  # Limit search depth
        config_path = current / ".canvas-config.json"
        if config_path.exists():
            return config_path
        parent = current.parent
        if parent == current:
            break
        current = parent

    return None


def load_config():
    """Load and validate configuration."""
    config_path = find_config()

    if not config_path:
        print("ERROR: .canvas-config.json not found", file=sys.stderr)
        print("Run setup or copy from templates/config.example.json", file=sys.stderr)
        sys.exit(1)

    try:
        config = json.loads(config_path.read_text())
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in config: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate required fields
    required = ["canvas_base_url", "cookies_file", "courses"]
    missing = [f for f in required if f not in config]
    if missing:
        print(f"ERROR: Missing required fields: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    # Resolve relative paths
    config_dir = config_path.parent
    cookies_path = Path(config["cookies_file"])
    if not cookies_path.is_absolute():
        cookies_path = config_dir / cookies_path
    config["cookies_file_resolved"] = str(cookies_path.resolve())

    return config


def main():
    parser = argparse.ArgumentParser(description="Load Canvas configuration")
    parser.add_argument("--canvas-url", action="store_true", help="Print Canvas base URL")
    parser.add_argument("--cookies-file", action="store_true", help="Print cookies file path")
    parser.add_argument("--courses", action="store_true", help="Print courses as JSON")
    parser.add_argument("--course-folders", action="store_true", help="Print folder names")
    parser.add_argument("--summarization-backend", action="store_true", help="Print summarization backend")
    parser.add_argument("--gemini-model", action="store_true", help="Print gemini model")
    parser.add_argument("--reasoning-backend", action="store_true", help="Print reasoning backend")
    parser.add_argument("--codex-model", action="store_true", help="Print codex model")
    parser.add_argument("--validate", action="store_true", help="Validate config and exit")

    args = parser.parse_args()

    config = load_config()

    if args.validate:
        print("Config valid", file=sys.stderr)
        sys.exit(0)
    elif args.canvas_url:
        print(config["canvas_base_url"])
    elif args.cookies_file:
        print(config["cookies_file_resolved"])
    elif args.courses:
        print(json.dumps(config["courses"]))
    elif args.course_folders:
        folders = [c["folder"] for c in config["courses"]]
        print(" ".join(folders))
    elif args.summarization_backend:
        print(config.get("summarization_backend", "claude"))
    elif args.gemini_model:
        print(config.get("gemini_model", "gemini-3-flash-preview"))
    elif args.reasoning_backend:
        print(config.get("reasoning_backend", "claude"))
    elif args.codex_model:
        print(config.get("codex_model", "gpt-5.2-codex-xhigh"))
    else:
        # Print full config
        print(json.dumps(config, indent=2))


if __name__ == "__main__":
    main()
