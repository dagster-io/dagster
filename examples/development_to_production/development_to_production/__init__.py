import sys

from development_to_production.repository import get_repo, repo

for name in ["a", "b", "c"]:
    setattr(sys.modules[__name__], name, get_repo(name))
