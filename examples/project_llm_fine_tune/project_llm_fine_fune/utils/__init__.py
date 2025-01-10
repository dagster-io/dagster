import json
from typing import Generator, Iterator


def write_openai_file(file_name: str, data: Iterator):
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
    """Reads the contents of a file

    Args:
        file_name (str): name of the input file

    Returns:
        Generator: records

    """
    with open(file_name, "r") as training_file:
        for line in training_file:
            yield dict(line.strip())
