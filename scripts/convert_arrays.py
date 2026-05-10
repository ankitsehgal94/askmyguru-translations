#!/usr/bin/env python3
"""
Convert flat translations from numeric-decomposed format to array-as-value
format, matching the backend's preferred wire shape.

Input:
    {
        "hashValue": "...",
        "translation": {
            "profile.deleteAccount.consequences.0": "Item 1",
            "profile.deleteAccount.consequences.1": "Item 2",
            "profile.deleteAccount.title": "Title"
        }
    }

Output:
    {
        "hashValue": "...",
        "translation": {
            "profile.deleteAccount.consequences": ["Item 1", "Item 2"],
            "profile.deleteAccount.title": "Title"
        }
    }

The transform groups numeric-suffix keys (.0, .1, ...) under their parent
path and emits a single array entry. Non-numeric leaves are passed through.
"""
import json
import sys
import hashlib
import re


NUMERIC_SUFFIX = re.compile(r"^(.+)\.(\d+)$")


def collapse_arrays(flat):
    """Merge keys like 'a.b.0', 'a.b.1' into 'a.b': [..., ...]."""
    # Bucket: parent path → ordered dict of {index: value}
    buckets = {}
    pass_through = {}

    for key, value in flat.items():
        m = NUMERIC_SUFFIX.match(key)
        if m:
            parent, idx = m.group(1), int(m.group(2))
            buckets.setdefault(parent, {})[idx] = value
        else:
            pass_through[key] = value

    out = dict(pass_through)
    for parent, items in buckets.items():
        # Reconstruct sorted list (assumes contiguous indices)
        max_idx = max(items.keys())
        arr = [items.get(i) for i in range(max_idx + 1)]
        out[parent] = arr

    return out


def main():
    if len(sys.argv) < 2:
        print("Usage: convert_arrays.py <input.json>", file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1], encoding="utf-8") as f:
        data = json.load(f)

    if "translation" not in data:
        print(f"{sys.argv[1]}: no 'translation' field, skipping",
              file=sys.stderr)
        sys.exit(0)

    collapsed = collapse_arrays(data["translation"])
    content = json.dumps(collapsed, sort_keys=True, ensure_ascii=False)
    hash_value = hashlib.sha256(content.encode("utf-8")).hexdigest()

    output = {
        "hashValue": hash_value,
        "translation": collapsed,
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
