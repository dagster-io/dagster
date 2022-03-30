import re


def sanitize_family(family):
    # Trim the location name and remove special characters
    return re.sub(r"[^\w^\-]", "", family)[:255]
