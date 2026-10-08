from pathlib import Path
import argparse
import random
import re


# ==================================================
# Default configuration
# ==================================================

POEMS_DIR = Path("poems")
DEFAULT_COLLECTION = "Book 1"
DEFAULT_CONTENTS_FILE = Path("collections/book-01/contents.md")


# ==================================================
# Read metadata from a poem
# ==================================================

def read_metadata(file_path):
    text = file_path.read_text(encoding="utf-8")

    # Find HTML-comment metadata block
    match = re.search(
        r"<!--\s*(.*?)\s*-->",
        text,
        re.DOTALL
    )

    if not match:
        return None

    metadata_text = match.group(1)

    metadata = {}

    # ----------------------------------------------
    # Read simple fields
    # ----------------------------------------------

    for line in metadata_text.splitlines():

        line = line.strip()

        if not line or line.startswith("-"):
            continue

        match = re.match(
            r'^([\w_]+):\s*["\']?(.*?)["\']?\s*$',
            line
        )

        if match:
            key = match.group(1)
            value = match.group(2).strip()

            value = value.strip('"').strip("'")

            metadata[key] = value

    # ----------------------------------------------
    # Read collections
    # ----------------------------------------------

    collections = []

    collections_match = re.search(
        r"collections:\s*((?:\s*-\s*.*\n?)+)",
        metadata_text
    )

    if collections_match:

        for line in collections_match.group(1).splitlines():

            match = re.match(
                r"\s*-\s*['\"]?(.*?)['\"]?\s*$",
                line
            )

            if match:
                collection = (
                    match.group(1)
                    .strip()
                    .strip('"')
                    .strip("'")
                )

                collections.append(collection)

    metadata["collections"] = collections

    # ----------------------------------------------
    # Read book_order
    # ----------------------------------------------

    book_order_match = re.search(
        r"book_order:\s*(\d+)",
        metadata_text
    )

    if book_order_match:
        metadata["book_order"] = int(
            book_order_match.group(1)
        )
    else:
        metadata["book_order"] = None

    return metadata


# ==================================================
# Find poems belonging to a collection
# ==================================================

def find_poems(collection_name):

    poems = []

    if not POEMS_DIR.exists():

        print(
            f"ERROR: The '{POEMS_DIR}' folder was not found."
        )

        return poems

    for file_path in sorted(POEMS_DIR.glob("*.md")):

        metadata = read_metadata(file_path)

        if not metadata:
            print(
                f"WARNING: No metadata found: "
                f"{file_path}"
            )
            continue

        collections = metadata.get(
            "collections",
            []
        )

        if collection_name not in collections:
            continue

        poems.append({
            "file": file_path,
            "metadata": metadata
        })

    return poems


# ==================================================
# Validate book order
# ==================================================

def validate_order(poems):

    missing_order = []
    order_map = {}

    for poem in poems:

        order = poem["metadata"].get(
            "book_order"
        )

        if order is None:

            missing_order.append(
                poem["file"].name
            )

        else:

            order_map.setdefault(
                order,
                []
            ).append(
                poem["file"].name
            )

    # ----------------------------------------------
    # Missing order
    # ----------------------------------------------

    if missing_order:

        print("\nWARNING: These poems have no book_order:")

        for filename in missing_order:
            print(f"  - {filename}")

    # ----------------------------------------------
    # Duplicate order
    # ----------------------------------------------

    duplicates = {
        order: files
        for order, files in order_map.items()
        if len(files) > 1
    }

    if duplicates:

        print("\nWARNING: Duplicate book_order values:")

        for order, files in duplicates.items():

            print(
                f"  Order {order}:"
            )

            for filename in files:
                print(
                    f"    - {filename}"
                )


# ==================================================
# Sort poems
# ==================================================

def sort_poems(poems, random_order=False):

    if random_order:

        random.shuffle(poems)

    else:

        # Poems without book_order go to the end.
        poems.sort(
            key=lambda poem: (
                poem["metadata"].get(
                    "book_order"
                )
                if poem["metadata"].get(
                    "book_order"
                ) is not None
                else 999999
            )
        )

    return poems


# ==================================================
# Create contents
# ==================================================

def create_contents(
    poems,
    collection_name
):

    lines = [
        "# Contents",
        "",
        f"## {collection_name}",
        ""
    ]

    for number, poem in enumerate(
        poems,
        start=1
    ):

        metadata = poem["metadata"]

        title = metadata.get(
            "title",
            poem["file"].stem
        )

        english_title = metadata.get(
            "english_title",
            ""
        )

        if english_title:

            display_title = (
                f"{title} — {english_title}"
            )

        else:

            display_title = title

        # Relative path from collections/book-01/
        link = (
            f"../../poems/"
            f"{poem['file'].name}"
        )

        lines.append(
            f"{number}. "
            f"[{display_title}]({link})"
        )

        lines.append("")

    return "\n".join(lines)


# ==================================================
# Main program
# ==================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Generate a poetry collection "
            "contents.md file."
        )
    )

    parser.add_argument(
        "--collection",
        default=DEFAULT_COLLECTION,
        help=(
            "Collection name, e.g. "
            '"Book 1"'
        )
    )

    parser.add_argument(
        "--random",
        action="store_true",
        help=(
            "Randomly shuffle the selected poems."
        )
    )

    parser.add_argument(
        "--preview",
        action="store_true",
        help=(
            "Preview the generated contents "
            "without changing the file."
        )
    )

    parser.add_argument(
        "--output",
        default=str(DEFAULT_CONTENTS_FILE),
        help=(
            "Output Markdown file."
        )
    )

    args = parser.parse_args()

    # ----------------------------------------------
    # Find poems
    # ----------------------------------------------

    poems = find_poems(
        args.collection
    )

    if not poems:

        print(
            f"No poems found for "
            f'"{args.collection}".'
        )

        return

    print(
        f"\nFound {len(poems)} poem(s) "
        f"for {args.collection}."
    )

    # ----------------------------------------------
    # Validate order
    # ----------------------------------------------

    if not args.random:

        validate_order(poems)

    # ----------------------------------------------
    # Sort / shuffle
    # ----------------------------------------------

    poems = sort_poems(
        poems,
        random_order=args.random
    )

    # ----------------------------------------------
    # Generate contents
    # ----------------------------------------------

    contents = create_contents(
        poems,
        args.collection
    )

    # ----------------------------------------------
    # Preview
    # ----------------------------------------------

    if args.preview:

        print("\n" + "=" * 50)
        print("PREVIEW")
        print("=" * 50)
        print()
        print(contents)
        print("=" * 50)

        return

    # ----------------------------------------------
    # Write file
    # ----------------------------------------------

    output_file = Path(
        args.output
    )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file.write_text(
        contents,
        encoding="utf-8"
    )

    print(
        f"\nGenerated:"
    )

    print(
        f"  {output_file}"
    )

    print(
        f"  {len(poems)} poem(s)"
    )

    if args.random:

        print(
            "  Order: RANDOM"
        )

    else:

        print(
            "  Order: book_order"
        )


if __name__ == "__main__":
    main()
