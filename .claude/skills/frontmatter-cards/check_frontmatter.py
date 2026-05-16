#!/usr/bin/env python3
"""
Claude Code PostToolUse hook.
Validates frontmatter after any Edit/Write to content/posts/*.md.
Reads tool event from stdin as JSON; prints warnings to stderr.
Never exits non-zero (must not block Claude).
"""
import sys
import json


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    tool_input = data.get("tool_input", data.get("input", {}))
    file_path = tool_input.get("file_path", "")

    if not file_path or "content/posts/" not in file_path or not file_path.endswith(".md"):
        return

    try:
        with open(file_path) as f:
            content = f.read()
    except FileNotFoundError:
        return

    if not content.startswith("---"):
        print(f"[hook] WARNING: {file_path} has no YAML frontmatter", file=sys.stderr)
        return

    end = content.find("---", 3)
    fm = content[3:end] if end > 0 else content[3:]

    required = ["title:", "date:", "draft:", "tags:", "categories:"]
    missing = [k for k in required if k not in fm]

    if missing:
        print(
            f"[hook] WARNING: {file_path} is missing frontmatter fields: "
            + ", ".join(m.rstrip(":") for m in missing),
            file=sys.stderr,
        )

    # Warn if draft:false is set without a description
    if "draft: false" in fm and "description:" not in fm:
        print(
            f"[hook] WARNING: {file_path} is marked draft:false but has no description field",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
    sys.exit(0)
