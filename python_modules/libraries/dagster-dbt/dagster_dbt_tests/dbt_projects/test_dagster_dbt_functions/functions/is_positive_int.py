import re


def main(a_string):
    return 1 if re.search(r"^[0-9]+$", a_string or "") else 0
