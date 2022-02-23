import pandas as pd
from dagster import io_manager, IOManager


def DbtModelIOManager(IOManager):
    def handle_output(context, obj):
        pass

    def load_input(context):
        model_name = context.upstream_output.output_def.name
