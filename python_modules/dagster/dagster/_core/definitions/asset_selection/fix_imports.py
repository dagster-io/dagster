def fix_imports(file_path):
    with open(file_path, "r") as file:
        lines = file.readlines()
    updated_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if "if sys.version_info[1] > 5:" in line or 'if "." in __name__:' in line:
            updated_lines.append(lines[i + 1].strip())
            i += 4
        else:
            updated_lines.append(line)
            i += 1
    with open(file_path, "w") as file:
        file.writelines(updated_lines)


def find_and_replace(file_path, target_text, replacement_text):
    with open(file_path, "r") as file:
        file_contents = file.read()

    updated_contents = file_contents.replace(target_text, replacement_text)

    with open(file_path, "w") as file:
        file.write(updated_contents)


def add_lines_to_start(file_path, lines_to_add):
    with open(file_path, "r") as file:
        original_content = file.readlines()

    updated_content = lines_to_add + original_content

    with open(file_path, "w") as file:
        file.writelines(updated_content)


files = [
    "AssetSelectionLexer.py",
    "AssetSelectionListener.py",
    "AssetSelectionParser.py",
    "AssetSelectionVisitor.py",
]

for file in files:
    fix_imports(file)
    if file == "AssetSelectionParser.py":
        add_lines_to_start(
            file,
            [
                "from .AssetSelectionListener import AssetSelectionListener\n",
                "from .AssetSelectionVisitor import AssetSelectionVisitor\n",
            ],
        )
        find_and_replace(
            file,
            "ParseTreeListener",
            "AssetSelectionListener",
        )
        find_and_replace(
            file,
            "ParseTreeVisitor",
            "AssetSelectionVisitor",
        )
