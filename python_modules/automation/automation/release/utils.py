from collections import defaultdict


def format_module_versions(module_versions):
    nightlies = defaultdict(list)
    versions = defaultdict(list)

    for module_name, module_version in module_versions.items():
        nightlies[module_version['__nightly__']].append(module_name)
        versions[module_version['__version__']].append(module_name)

    res = '\n'
    for key, libraries in nightlies.items():
        res += '%s:\n\t%s\n\n' % (key, '\n\t'.join(libraries))

    res += '\n'

    for key, libraries in versions.items():
        res += '%s:\n\t%s\n' % (key, '\n\t'.join(libraries))

    return res
