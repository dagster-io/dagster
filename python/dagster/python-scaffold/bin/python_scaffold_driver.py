# pylint: disable=E0401, C0413

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import python_scaffold
python_scaffold.main(sys.argv)
