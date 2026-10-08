```python
from pathlib import Path
import re

# --------------------------------------------------
# Configuration
# --------------------------------------------------

POEMS_DIR = Path("poems")
CONTENTS_FILE = Path("collections/book-01/contents.md")
COLLECTION_NAME = "Book 1"


# --------------------------------------------------
# Read metadata from a poem
# --------------------------------------------------

def read_metadata(file_path):
    text = file_path.read_text(encoding="utf-8")

    # Find the HTML-comment metadata block
    match = re.search(
        r"<!--\s*(.*?)\s*-->",
        text,
        re.DOTALL
    )

    if not match:
        return None

    metadata_text = match.group(1)

    metadata = {}

    for line in metadata_text.splitlines():
        line = line.strip()

        if not line or line.startswith("-"):
            continue

        match = re.match(r'^([\w_]+):\s*["\']?(.*?)["\']?\s*$', line)

        if match:
            key = match.group(1)
            value = match.group(2).strip().strip('"').strip("'")
            metadata[key] = value

    # Extract collections
    collections_match = re.search(
        r"collections:\s*((?:\s*-\s*.*\n?)+)",
        metadata_text
    )

    collections = []

    if collections_match:
        for line in collections_match.group(1).splitlines():
            match = re.match(r"\s*-\s*['\"]?(.*?)['\"]?\s*$", line)
            if match:
                collections.append(
                    match.group(1).strip().strip('"').strip("'")
                )

    metadata["collections"] = collections

    # Extract book_order
    book_order_match = re.search(
        r"book_order:\s*(\d+)",
        metadata_text
    )

    if book_order_match:
        metadata["book_order"] = int(book_order_match.group(1))
    else:
        metadata["book_order"] = 9999

    return metadata


# --------------------------------------------------
# Find selected poems
# --------------------------------------------------

poems = []

for file_path in POEMS_DIR.glob("*.md"):

    metadata = read_metadata(file_path)

    if not metadata:
        continue

    if COLLECTION_NAME not in metadata.get("collections", []):
        continue

    poems.append({
        "file": file_path,
        "metadata": metadata
    })


# --------------------------------------------------
# Sort by book order
# --------------------------------------------------

poems.sort(
    key=lambda poem: poem["metadata"].get("book_order", 9999)
)


# --------------------------------------------------
# Generate contents.md
# --------------------------------------------------

lines = [
    "# Contents",
    "",
    f"## {COLLECTION_NAME}",
    ""
]

for number, poem in enumerate(poems, start=1):

    metadata = poem["metadata"]

    title = metadata.get("title", poem["file"].stem)
    english_title = metadata.get("english_title", "")

    if english_title:
        display_title = f"{title} — {english_title}"
    else:
        display_title = title

    link = f"../../poems/{poem['file'].name}"

    lines.append(
        f"{number}. [{display_title}]({link})"
    )
    lines.append("")


# --------------------------------------------------
# Write file
# --------------------------------------------------

CONTENTS_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

CONTENTS_FILE.write_text(
    "\n".join(lines),
    encoding="utf-8"
)

print(
    f"Generated {CONTENTS_FILE} "
    f"with {len(poems)} selected poem(s)."
)
```
