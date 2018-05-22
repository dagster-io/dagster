import json

from dagster import check

import dagster.core

from .flatten import flatten_json_to_dataframes


class QhpJsonPivotPoints:
    PROVIDERS = '@.*'
    ADDRESSES = '@.*.addresses.*'
    NAMES = '@.*.name'
    PLANS = '@.*.plans.*'
    PLAN_YEARS = '@.*.plans.*.years.*'


qhp_json_pivot_points = [
    QhpJsonPivotPoints.PROVIDERS,
    QhpJsonPivotPoints.ADDRESSES,
    QhpJsonPivotPoints.NAMES,
    QhpJsonPivotPoints.PLANS,
    QhpJsonPivotPoints.PLAN_YEARS,
]


def define_qhp_input(table_field_expr):
    check.str_param(table_field_expr, 'table_field_expr')

    def flatten_table_field(context, arg_dict):
        path = check.str_elem(arg_dict, 'path')
        with open(path) as file_obj:
            json_object = json.load(file_obj)
        qhp_providers = flatten_json_to_dataframes(json_object, qhp_json_pivot_points)
        df = qhp_providers[table_field_expr]
        context.metric('rows', df.shape[0])
        return df

    return dagster.core.file_input_definition(
        name='qhp_json_input',
        input_fn=flatten_table_field,
    )
