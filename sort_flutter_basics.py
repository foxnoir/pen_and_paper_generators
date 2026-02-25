#!/usr/bin/env python3
"""Sort flutter_basics.csv: 1) Was ist, 2) Was bedeutet, 3) Other general, 4) Flutter, 5) Git, 6) Rest."""
import csv
import re
import sys

CSV_PATH = "flutter_basics.csv"

# Keywords for classification (lowercase)
FLUTTER_KEYWORDS = [
    "flutter", "widget", "state", "buildcontext", "riverpod", "provider",
    "setstate", "inheritedwidget", "element tree", "render tree", "widget tree",
    "stateless", "stateful", "dart", "key", "valuekey", "globalkey", "uniquekey",
    "objectkey", "layout", "constraints", "build()", "dispose", "mounted",
    "bloc", "cubit", "context.", "scaffold", "materialapp", "gesturedetector",
    "listview", "column", "row", "container", "text(", "elevatedbutton",
    "async gap", "future", "stream", "animation", "ticker", "overlay",
    "navigator", "theme.of", "mediaguery", "keyboard", "focus", "scroll",
    "sliver", "repaintboundary", "const ", "hot reload", "hot restart",
]

GIT_KEYWORDS = [
    "git", "commit", "branch", "merge", "rebase", "remote", "push", "pull",
    "stash", "checkout", "clone", "fetch", "origin", "merge conflict",
]


def normalize(q: str) -> str:
    """Normalize for matching: lowercase, replace <br> with space."""
    if not q:
        return ""
    s = q.lower().replace("<br>", " ").replace("\n", " ")
    # collapse spaces
    s = re.sub(r"\s+", " ", s)
    return s


def is_was_ist(q_norm: str, q_orig: str) -> bool:
    """Definition-style: Was ist, Was sind, – was ist, Definition."""
    if not q_norm:
        return False
    # "Was ist X" or "X – was ist"
    if re.search(r"\bwas ist\b", q_norm):
        return True
    if re.search(r"\bwas sind\b", q_norm):
        return True
    if re.search(r"–\s*was ist\b", q_norm) or re.search(r"-\s*was ist\b", q_norm):
        return True
    if "was ist das" in q_norm or "definition" in q_norm:
        return True
    if re.search(r"was ist (der|die|das|er|sie)\b", q_norm):
        return True
    return False


def is_was_bedeutet(q_norm: str) -> bool:
    """Meaning-style: was bedeutet, was heißt, was besagt."""
    if "was bedeutet" in q_norm or "was heißt" in q_norm or "was besagt" in q_norm:
        return True
    return False


def is_flutter(q_norm: str) -> bool:
    for k in FLUTTER_KEYWORDS:
        if k in q_norm:
            return True
    return False


def is_git(q_norm: str) -> bool:
    for k in GIT_KEYWORDS:
        if k in q_norm:
            return True
    return False


def tier(question: str) -> tuple[int, int, str]:
    """Return (sort_priority, sub_priority, group_name). Lower = earlier in file.
    Sub_priority: 0 = Frage *beginnt* mit 'Was ist'/'Was sind', 1 = enthält nur irgendwo 'was ist'."""
    q_norm = normalize(question)
    q_stripped = q_norm.lstrip()
    starts_with_was_ist = (
        q_stripped.startswith("was ist ")
        or q_stripped.startswith("was sind ")
        or re.match(r"^was ist (der|die|das)\b", q_stripped)
    )
    if is_was_ist(q_norm, question):
        sub = 0 if starts_with_was_ist else 1
        return (0, sub, "was_ist")
    if is_was_bedeutet(q_norm):
        return (1, 0, "was_bedeutet")
    if is_git(q_norm):
        return (4, 0, "git")
    if is_flutter(q_norm):
        return (3, 0, "flutter")
    return (2, 0, "general")


def main():
    path = CSV_PATH
    rows: list[tuple[int, int, str, list]] = []  # (tier, sub, group, row cells)

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";", quotechar='"', doublequote=True)
        for row in reader:
            if len(row) < 2:
                continue
            q = row[0]
            t, sub, group = tier(q)
            rows.append((t, sub, group, row))

    # Sort: tier, then sub (Was ist X first), then by question text
    rows.sort(key=lambda x: (x[0], x[1], x[3][0]))

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for _, _, _, row in rows:
            writer.writerow(row)

    # Summary
    from collections import Counter
    counts = Counter(g for (_, _, g, _) in rows)
    print("Sorted. Counts:", dict(counts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
