# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_int_field 1'] = '''{
  int_field: [Int] 
}'''

snapshots['test_int_fails 1'] = '''{
  int_field: [Int] 
}'''

snapshots['test_default_arg 1'] = '''{
  int_field?: [Int]  default=2
}'''

snapshots['test_print_schema 1'] = '''{
  nested: {
    int_field: [Int] 
  }
}'''

snapshots['test_print_schema 2'] = '''{
  nested?: {
    int_field?: [Int]  default=3
  } default={'int_field': 3}
}'''

snapshots['test_print_schema 3'] = '''{
  nested?: {
    int_field?: [Int] 
  } default={}
}'''
