from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *  # pylint: disable=W0622,W0401

import check

from .solid_defs import Solid


class DagsterPipeline:
    def __init__(self, name, solids):
        self.name = check.str_param(name, 'name')
        self.solids = check.list_param(solids, 'solids', of_type=Solid)
