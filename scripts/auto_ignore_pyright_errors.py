#!python

# this script allows automatically inserting pyright: ignore (rule) comments for pyright error
# it can be used like this: make pyright | ./scripts/auto_ignore_pyright_errors.py
import re
import sys

# Regular expression to match pyright error lines
error_pattern = re.compile(
    r"(?P<file_name>.*?):(?P<line_number>\d+):\d+ - error:.*?(\((?P<rules_single>[^)]+)\))?$"
)

# Additional regex to match the second line of a multi-line error message for rules
rule_line_pattern = re.compile(r"^.*\((?P<rules>[^)]+)\)$")


UNFIXABLE_RULES = {"reportUnnecessaryTypeIgnoreComment"}


def main():
    # Dictionary to store errors by file and line
    errors = {}

    # Read from standard input
    previous_line = None
    for stdin_line in sys.stdin:
        line = stdin_line.strip()
        if previous_line is None:
            match = error_pattern.match(line)
            if match:
                file_path = match.group("file_name")
                line_number = int(match.group("line_number"))
                rule = match.group("rules_single")

                if file_path not in errors:
                    errors[file_path] = {}
                if line_number not in errors[file_path]:
                    errors[file_path][line_number] = []

                # If rule is found in the first line itself, add it
                if rule:
                    errors[file_path][line_number].append(rule)

                # Store the line for potential multi-line handling
                previous_line = line
            else:
                # Reset if not a match (should not happen normally)
                previous_line = None
        else:
            # This line is expected to be the second line of the error message
            match = rule_line_pattern.match(line)
            if match:
                rule = match.group("rules").strip()
                # Only append if it's a valid rule
                if rule and "pyright:" not in rule:
                    file_path = error_pattern.match(previous_line).group("file_name")
                    line_number = int(error_pattern.match(previous_line).group("line_number"))
                    errors[file_path][line_number].append(rule)

            # Reset for the next error message
            previous_line = None

    # Process each file and add ignore comments
    for file_path, lines in errors.items():
        try:
            with open(file_path) as file:
                content = file.readlines()

            for line_number, rules in sorted(lines.items(), reverse=True):
                # Ensure only unique rules are added
                unique_rules = sorted(set(rules) - UNFIXABLE_RULES)
                ignore_comment = f"  # pyright: ignore ({', '.join(unique_rules)})\n"
                content[line_number - 1] = content[line_number - 1].rstrip() + ignore_comment

            with open(file_path, "w") as file:
                file.writelines(content)

            update_summary = {line: rules for line, rules in lines.items()}

            if update_summary:
                for line, rules in update_summary.items():
                    print(f"{file_path}:{line} - ignored {rules}")  # noqa

        except Exception as e:
            print(f"Error processing {file_path}: {e}")  # noqa


if __name__ == "__main__":
    main()
