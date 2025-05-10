import json
from collections.abc import Generator


def write_openai_file(file_name: str, data: list):
    """Writes the contents of list to file.

    Args:
        file_name (str): name of the output file
        data (list): data to write to file

    """
    with open(file_name, "w") as output_file:
        for i, row in enumerate(data):
            output_file.write(json.dumps(row))
            if i < len(data) - 1:
                output_file.write("\n")


def read_openai_file(file_name: str) -> Generator:
    """Reads the contents of a file.

    Args:
        file_name (str): name of the input file

    Returns:
        Generator: records of the jsonl file as dicts

    """
    with open(file_name) as training_file:
        for line in training_file:
            if line.strip():
                yield json.loads(line)
