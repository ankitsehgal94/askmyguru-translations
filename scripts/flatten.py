#!/usr/bin/env python3
"""
Convert nested translations JSON to backend-flat format.

Input shape:
    {
        "version": "v25",
        "language": "hi-IN",
        "translations": {
            "chat": { "screen": { "deleteChatMenu": "..." } }
        }
    }

Output shape (matches backend's contract):
    {
        "hashValue": "<sha256 of content>",
        "translation": {
            "chat.screen.deleteChatMenu": "..."
        }
    }
"""
import json
import sys
import hashlib


def flatten(obj, prefix=""):
    """Recursively flatten a nested object/list into dotted-key format."""
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else k
            out.update(flatten(v, key))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            key = f"{prefix}.{i}" if prefix else str(i)
            out.update(flatten(v, key))
    else:
        out[prefix] = obj
    return out


def main():
    if len(sys.argv) < 2:
        print("Usage: flatten.py <input.json>", file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1], encoding="utf-8") as f:
        data = json.load(f)

    if "translations" not in data:
        print(f"{sys.argv[1]}: already flat or unknown shape, skipping",
              file=sys.stderr)
        sys.exit(0)

    flat = flatten(data["translations"])
    content = json.dumps(flat, sort_keys=True, ensure_ascii=False)
    hash_value = hashlib.sha256(content.encode("utf-8")).hexdigest()

    output = {
        "hashValue": hash_value,
        "translation": flat,
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
