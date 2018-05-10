import solidic
import solidic_pandas as solidic_pd

from .qhp_input import (define_qhp_input, QhpJsonPivotPoints)


def define_pipeline():
    plans = solidic_pd.dataframe_solid(
        name='plans',
        inputs=[
            define_qhp_input(
                input_name='qhp_json_input', table_field_expr=QhpJsonPivotPoints.PLANS
            )
        ],
    )

    plan_years = solidic_pd.dataframe_solid(
        name='plan_years',
        inputs=[
            define_qhp_input(
                input_name='qhp_json_input', table_field_expr=QhpJsonPivotPoints.PLAN_YEARS
            )
        ],
    )

    insurance = solidic_pd.dataframe_solid(
        name='insurance',
        transform_fn=insurance_tranform,
        inputs=[
            solidic_pd.depends_on(plans),
            solidic_pd.depends_on(plan_years),
        ],
    )

    return solidic.pipeline(solids=[plans, plan_years, insurance])


def insurance_tranform(plans, plan_years):
    insurance_df = plans.merge(
        plan_years[['parent_id', 'value']], left_on='id_', right_on='parent_id'
    )

    insurance_df.rename(columns={'plan_id': 'HIOS-PLAN-ID'}, inplace=True)
    insurance_df.drop(['plan_id_type'], axis=1, inplace=True)
    insurance_df.rename(columns={'parent_id_x': 'parent_id'}, inplace=True)
    insurance_df.drop(['parent_id_y'], axis=1, inplace=True)
    insurance_df['plan_year'] = insurance_df['value'].astype(str)
    insurance_df['uid'] = (
        "HIOS-PLAN-ID-" + insurance_df['HIOS-PLAN-ID'] + "-" + insurance_df['plan_year']
    )
    insurance_df['qhp_provider_id'] = insurance_df["parent_id"]
    insurance_df = insurance_df[[
        "uid", "network_tier", "HIOS-PLAN-ID", "plan_year", "qhp_provider_id"
    ]]
    return insurance_df
