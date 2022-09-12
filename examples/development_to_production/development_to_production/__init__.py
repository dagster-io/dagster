import sys
from development_to_production.repository import repo, get_repo

for name in ["a", "b", "c"]:
    setattr(sys.modules[__name__], name, get_repo(name))
