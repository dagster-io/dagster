import solidic
import solidic_pandas as solidic_pd

from .qhp_input import define_qhp_input


def define_pipeline():
    plans = solidic_pd.tabular_solid(
        name='plans',
        inputs=[define_qhp_input(input_name='qhp_json_input', table_field_expr='@.*.plans.*')],
    )

    return solidic.pipeline(solids=[plans])
