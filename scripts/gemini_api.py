#!/usr/bin/env python3
"""
Gemini API helper for PDF/image analysis.
Uses the google-genai SDK for efficient multimodal processing.

Usage:
    python3 gemini_api.py <file_path> "<prompt>" [-m MODEL] [-o OUTPUT]

Examples:
    python3 gemini_api.py lecture.pdf "Summarize this for exam prep"
    python3 gemini_api.py lecture.pdf "Summarize" -m gemini-2.5-flash
    python3 gemini_api.py diagram.png "Explain this" -o /tmp/result.md
"""

import argparse
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# Default model - gemini-3-flash-preview is recommended for best performance
DEFAULT_MODEL = "gemini-3-flash-preview"


def find_env_file():
    """Search for .env file in common locations."""
    search_paths = [
        Path.cwd() / ".env",                    # Current working directory
        Path(__file__).parent.parent / ".env",  # Plugin root
        Path(__file__).parent / ".env",         # Scripts directory
        Path.home() / ".env",                   # Home directory
    ]

    # Also check CANVAS_CONFIG for custom env path
    config_file = Path.cwd() / ".canvas-config.json"
    if config_file.exists():
        try:
            import json
            config = json.loads(config_file.read_text())
            custom_env = config.get("gemini_env_file")
            if custom_env:
                custom_path = Path(custom_env).expanduser()
                if not custom_path.is_absolute():
                    custom_path = Path.cwd() / custom_path
                search_paths.insert(0, custom_path)
        except Exception:
            pass

    for env_path in search_paths:
        if env_path.exists():
            return env_path
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Gemini API helper for PDF/image analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  python3 gemini_api.py lecture.pdf "Summarize for exam prep"
  python3 gemini_api.py slide.pdf "Extract key concepts" -m gemini-2.5-flash
  python3 gemini_api.py diagram.png "Explain this" -o /tmp/out.md

Available models:
  gemini-3-flash-preview  (default, recommended)
  gemini-2.5-flash
  gemini-2.5-pro
        """
    )
    parser.add_argument("file_path", help="Path to PDF or image file")
    parser.add_argument("prompt", help="Task/question for Gemini")
    parser.add_argument(
        "-m", "--model",
        default=DEFAULT_MODEL,
        help=f"Gemini model to use (default: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "-o", "--output",
        default="/tmp/gemini-result.md",
        help="Output file path (default: /tmp/gemini-result.md)"
    )

    args = parser.parse_args()

    file_path = Path(args.file_path).expanduser().resolve()
    prompt = args.prompt
    model = args.model
    output_file = Path(args.output)

    # Load API key from .env
    env_file = find_env_file()
    if env_file and load_dotenv:
        load_dotenv(env_file)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found.", file=sys.stderr)
        print("Set it in .env file or as environment variable.", file=sys.stderr)
        sys.exit(1)

    # Validate file
    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    # Determine MIME type
    suffix = file_path.suffix.lower()
    mime_types = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    mime_type = mime_types.get(suffix)
    if not mime_type:
        print(f"ERROR: Unsupported file type: {suffix}", file=sys.stderr)
        sys.exit(1)

    # Import and initialize
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("ERROR: google-genai not installed. Run: pip install google-genai", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # Process file
    file_size = file_path.stat().st_size
    print(f"Using model: {model}", file=sys.stderr)

    try:
        if file_size > 10 * 1024 * 1024:  # > 10MB: use Files API
            print(f"Uploading large file ({file_size / 1024 / 1024:.1f} MB)...", file=sys.stderr)
            uploaded = client.files.upload(file=file_path)
            response = client.models.generate_content(
                model=model,
                contents=[uploaded, prompt],
            )
        else:  # Inline for smaller files
            response = client.models.generate_content(
                model=model,
                contents=[
                    types.Part.from_bytes(
                        data=file_path.read_bytes(),
                        mime_type=mime_type,
                    ),
                    prompt,
                ],
            )

        result = response.text

        # Write to output file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(result)
        print(f"Output written to: {output_file}", file=sys.stderr)

        # Also print to stdout for immediate use
        print(result)

    except Exception as e:
        print(f"ERROR: Gemini API call failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
