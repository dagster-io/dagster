import os
import sys
import time
from datetime import datetime

from dagster import (
    InputDefinition,
    ModeDefinition,
    Output,
    OutputDefinition,
    String,
    pipeline,
    solid,
)
from dagster.core.definitions.executor import default_executors

NUM_LOOP = 120
REP_INTERVAL = 0.5


@solid(output_defs=[OutputDefinition(String, 'out_1'), OutputDefinition(String, 'out_2')])
def spawn(_):
    yield Output('A', 'out_1')
    yield Output('B', 'out_2')


@solid(input_defs=[InputDefinition('name', String)])
def spew(_, name):
    i = 0
    while i < NUM_LOOP:
        print('{} {} OUT {}: {}'.format(os.getpid(), name, i, datetime.now()), file=sys.stdout)
        print('{} {} ERROR {}: {}'.format(os.getpid(), name, i, datetime.now()), file=sys.stderr)
        time.sleep(REP_INTERVAL)
        i += 1


@pipeline(
    description='Demo pipeline that streams out logs to the compute logs stdout/stderr.',
    mode_defs=[ModeDefinition(executor_defs=default_executors)],
)
def stdout_spew_pipeline():
    out_1, out_2 = spawn()
    spew(name=out_1)
    spew(name=out_2)
