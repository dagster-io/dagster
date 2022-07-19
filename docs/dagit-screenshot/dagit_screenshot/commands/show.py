from typing import Optional
import yaml
from dagit_screenshot.utils import load_spec_db


def show(spec_db_path: str, prefix: Optional[str]):
    spec_db = load_spec_db(spec_db_path)
    sorted_db = sorted(spec_db, key=lambda s: s["id"])
    filtered_db = [ s for s in sorted_db if not prefix or s["id"].startswith(prefix) ]
    print(yaml.dump(filtered_db))
