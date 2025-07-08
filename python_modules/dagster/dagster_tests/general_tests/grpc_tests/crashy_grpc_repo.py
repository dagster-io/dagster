import sys

import dagster as dg


@dg.repository
def crashy_repo():
    sys.exit(123)
