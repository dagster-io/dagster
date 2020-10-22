from collections import defaultdict


def format_module_versions(module_versions):
    versions = defaultdict(list)

    for module_name, module_version in module_versions.items():
        versions[module_version["__version__"]].append(module_name)

    res = "\n"

    for key, libraries in versions.items():
        res += "%s:\n\t%s\n" % (key, "\n\t".join(libraries))

    return res
