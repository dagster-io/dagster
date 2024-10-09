from pathlib import Path

# We want to group some kinds together in the docs
SPECIAL_KIND_ORDERS = [
    [
        "bronze",
        "silver",
        "gold",
    ],
    [
        "dag",
        "task",
    ],
    ["table", "view", "source", "seed", "file", "dashboard", "notebook"],
    [
        "csv",
        "pdf",
        "yaml",
    ],
]

ALL_SPECIAL_KINDS = [kind for order in SPECIAL_KIND_ORDERS for kind in order]

REPO_ROOT = Path(__file__).parent.parent.parent
OP_TAGS_FILE = (
    REPO_ROOT
    / "js_modules"
    / "dagster-ui"
    / "packages"
    / "ui-core"
    / "src"
    / "graph"
    / "OpTags.tsx"
)
KIND_TAGS_DOCS_FILE = (
    REPO_ROOT / "docs" / "content" / "concepts" / "metadata-tags" / "kind-tags.mdx"
)
DOCS_KIND_IMAGES_DEST = (
    REPO_ROOT
    / "docs"
    / "next"
    / "public"
    / "images"
    / "concepts"
    / "metadata-tags"
    / "kinds"
    / "icons"
)

KIND_LINE = (
    '| `{kind}`{kind_spacing}| <Image src="{image}" width={{20}} height={{20}} />{image_spacing}|'
)


def main() -> None:
    contents = OP_TAGS_FILE.read_text()

    all_current_kinds = set()
    imported_images = {}
    kind_images = {}

    # Parse the tsx op tags file to get the kinds and their images
    in_tag_type_section = False
    in_tag_images_section = False
    current_kind = None
    for line in contents.split("\n"):
        # Get the raw image imports
        if "import" in line:
            line_parts = line.split(" ")
            if len(line_parts) != 4:
                continue
            _, kind, __, image_raw = line_parts
            image = image_raw.split("'")[1]
            imported_images[kind] = image

        # Get the list of kinds
        if "export type KnownTagType" in line:
            in_tag_type_section = True
        elif in_tag_type_section:
            if len(line.strip()) == 0:
                in_tag_type_section = False
                continue
            all_current_kinds.add(line.split("'")[1])

        # Get the mapping of kinds to images
        if "export const KNOWN_TAGS" in line:
            in_tag_images_section = True
        elif in_tag_images_section:
            if len(line.strip()) == 0:
                in_tag_images_section = False
                continue
            if line.strip().endswith("{"):
                current_kind = line.split(":")[0].strip()
            elif "icon" in line:
                image_name = line.split(":")[1].strip()[:-1]
                kind_images[current_kind] = imported_images.get(image_name, None)

    kind_docs_images = {}

    # Copy the images to the docs folder & ignore kinds without images
    missing_kinds = set()
    for kind in all_current_kinds:
        if kind not in kind_images or not kind_images[kind]:
            print(f"Missing image for kind: {kind}")  # noqa: T201
            missing_kinds.add(kind)
        else:
            kind_image_path: Path = OP_TAGS_FILE.parent / kind_images[kind]
            kind_image_dest_path = DOCS_KIND_IMAGES_DEST / kind_image_path.name
            kind_image_dest_path.write_bytes(kind_image_path.read_bytes())
            kind_docs_images[kind] = "/" + str(
                kind_image_dest_path.relative_to(REPO_ROOT / "docs" / "next" / "public")
            )
    for kind in missing_kinds:
        all_current_kinds.remove(kind)

    # Build ordered list of kinds, with special kinds maintained in their groups & orderings
    sorted_rest_of_kinds = sorted(
        [kind for kind in all_current_kinds if kind not in ALL_SPECIAL_KINDS]
    )
    output = sorted_rest_of_kinds
    for kind_order in SPECIAL_KIND_ORDERS:
        output.extend([kind for kind in kind_order if kind in all_current_kinds])
    docs_file_contents = KIND_TAGS_DOCS_FILE.read_text()
    docs_file_new_contents = []

    # Rebuild the docs file with all kinds and images in the correct order
    in_kind_tags_section = False
    for line in docs_file_contents.split("\n"):
        if "| -----------------" in line:
            in_kind_tags_section = True
        elif in_kind_tags_section:
            if len(line.strip()) == 0:
                in_kind_tags_section = False

                for kind in output:
                    docs_file_new_contents.append(
                        KIND_LINE.format(
                            kind=kind,
                            kind_spacing=" " * (20 - len(kind)),
                            image=kind_docs_images.get(kind, ""),
                            image_spacing=" " * (100 - len(kind_docs_images.get(kind, ""))),
                        )
                    )

            else:
                continue
        docs_file_new_contents.append(line)

    KIND_TAGS_DOCS_FILE.write_text("\n".join(docs_file_new_contents))

    print(f"Generated {len(output)} kinds")  # noqa: T201


if __name__ == "__main__":
    main()
