import os
import tempfile

import pandas as pd
from bite_sized.dynamic_output import dynamic_output
from dagster.core.test_utils import instance_for_test


def test_dynamic_output():
    with tempfile.TemporaryDirectory() as tmp_dir:
        with instance_for_test(temp_dir=tmp_dir) as instance:
            assert dynamic_output.execute_in_process(
                instance=instance,
                run_config={"resources": {"io_manager": {"config": {"base_dir": tmp_dir}}}},
            ).success
