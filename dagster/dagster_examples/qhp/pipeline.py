import json
from collections import defaultdict

import numpy as np
import pandas as pd

from dagster import check

import dagster
import dagster.pandas_kernel as dagster_pd

from dagster.dagster_examples.qhp.qhp_input import (QhpJsonPivotPoints, define_qhp_input)


def unpack_row(row, fields):
    """Extract fields by name from row into obj.
    Fields with missing keys or null values are excluded
    All other fields are converted to strings.
    """
    obj = {}
    for field in fields:
        if field in row:
            if not row[field] is None:
                try:
                    if np.isnan(row[field]):
                        continue
                except:  # pylint: disable=W0702
                    pass

                if isinstance(row[field], list):
                    obj[field] = [str(item) for item in row[field]]
                else:
                    obj[field] = str(row[field])
    return obj


def define_pipeline():
    plans = dagster_pd.dataframe_solid(
        name='plans',
        inputs=[define_qhp_input(table_field_expr=QhpJsonPivotPoints.PLANS)],
    )

    plan_years = dagster_pd.dataframe_solid(
        name='plan_years',
        inputs=[define_qhp_input(table_field_expr=QhpJsonPivotPoints.PLAN_YEARS)],
    )

    addresses = dagster_pd.dataframe_solid(
        name='addresses',
        inputs=[define_qhp_input(table_field_expr=QhpJsonPivotPoints.ADDRESSES)],
    )

    providers = dagster_pd.dataframe_solid(
        name='providers',
        inputs=[define_qhp_input(table_field_expr=QhpJsonPivotPoints.PROVIDERS)],
    )

    languages = dagster_pd.dataframe_solid(
        name='languages',
        inputs=[dagster_pd.csv_input('languages_csv', delimiter='|')],
    )

    specialities = dagster_pd.dataframe_solid(
        name='specialities',
        inputs=[dagster_pd.csv_input('specialities_csv')],
    )

    insurance = dagster_pd.dataframe_solid(
        name='insurance',
        transform_fn=insurance_tranform,
        inputs=[
            dagster_pd.depends_on(plans),
            dagster_pd.depends_on(plan_years),
        ],
    )

    practices = dagster_pd.dataframe_solid(
        name='practices',
        transform_fn=practices_transform,
        inputs=[
            dagster_pd.depends_on(addresses),
            dagster_pd.depends_on(providers),
        ]
    )

    provider_languages_specialities = dagster_pd.dataframe_solid(
        name='provider_languages_specialities',
        transform_fn=provider_languages_specialities_transform,
        inputs=[
            dagster_pd.depends_on(providers),
            dagster_pd.depends_on(specialities),
            dagster_pd.depends_on(languages),
        ]
    )

    names = dagster_pd.dataframe_solid(
        name='names',
        inputs=[define_qhp_input(table_field_expr=QhpJsonPivotPoints.NAMES)],
    )

    practice_insurances = dagster_pd.dataframe_solid(
        name='practice_insurances',
        transform_fn=transform_practice_insurances,
        inputs=[
            dagster_pd.depends_on(insurance),
            dagster_pd.depends_on(practices),
        ]
    )

    return dagster.pipeline(
        name='qhp',
        solids=[
            plans,
            plan_years,
            addresses,
            providers,
            languages,
            specialities,
            insurance,
            practices,
            provider_languages_specialities,
            practice_insurances,
            names,
        ]
    )


def practices_transform(addresses, providers):
    practice_df = addresses.merge(
        providers,
        how='left',
        left_on='parent_id',
        right_on='id_',
        suffixes=('_address', '_provider')
    )
    practice_df.rename(
        columns={
            'address': 'street',
            'address_2': 'street2',
            'address2': 'street2',
            'parent_id': 'doctor_id',
            'id__provider': 'qhp_provider_id'
        },
        inplace=True
    )
    return practice_df


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


def extract_json_from_insurance_row(row):
    return {
        'uid': row['uid'],
        'network': {
            'tier': row['network_tier']
        },
        'plan': {
            'HIOS-PLAN-ID': row['HIOS-PLAN-ID']
        },
        'plan_year': row['plan_year'],
        'metadata': {
            'klass': 'BetterDoctor::DSF::Insurance'
        }
    }


def extract_json_from_practice_row(row):
    address = unpack_row(row, ['street', 'street2', 'city', 'state', 'zip'])
    address['type'] = 'visit'

    home_phone = {
        # Note: We're assuming all phones are landlines. Maybe better not to make this assumption
        'type': 'landline',
        'number': str(row['phone'])
    }
    return {
        'phones': [home_phone],
        'addresses': [address],
        'last_updated_on': row['last_updated_on'],
    }


def transform_practice_insurances(insurance, practices):
    practice_insurance_dict = defaultdict(list)
    for _i, row in practices.iterrows():
        new_row = extract_json_from_practice_row(row)

        new_row['insurances'] = [
            extract_json_from_insurance_row(row_j) for i, row_j in
            insurance[insurance.qhp_provider_id == row['qhp_provider_id']].iterrows()
        ]

        practice_insurance_dict[row['qhp_provider_id']].append(new_row)

    df_data = {
        'qhp_provider_id': [],
        'data_json': [],
    }

    for qhp_provider_id, json_rows in practice_insurance_dict.items():
        df_data['qhp_provider_id'].append(qhp_provider_id)
        df_data['data_json'] = json.dumps(json_rows)

    return pd.DataFrame(df_data)


def map_languages(values_str, language_dict):
    try:
        values = json.loads(values_str)
    except TypeError:
        return []

    try:
        return [language_dict[v] for v in values]
    except:  # pylint: disable=W0702
        return []


def create_language_dict(languages_df):
    language_dict = {}
    for _i, row in languages_df.iterrows():
        language_dict[row['LanguageName']] = row['ISO639-3Code']
    return language_dict


def provider_languages_specialities_transform(providers, specialities, languages):
    check.inst_param(specialities, 'specialities', pd.DataFrame)  # kill warning

    expected_columns = [
        'gender',
        'languages',
        'npi',
        'specialty',
        'last_updated_on',
    ]

    gender_map = {
        'Male': 'M',
        'Female': 'F',
        'M': 'M',
        'F': 'F',
        'Other': 'Other',
        '': None,
        None: None,
        np.nan: None,
    }

    output_df = providers[expected_columns + ['id_']][providers["type"] == "INDIVIDUAL"]
    output_df.rename(columns={'id_': 'qhp_provider_id'}, inplace=True)

    output_df['gender'] = output_df['gender'].map(lambda x: gender_map[x])

    #Replace languages with ISO codes
    language_dict = create_language_dict(languages)
    output_df['languages'] = output_df['languages'].map(lambda x: map_languages(x, language_dict))

    return output_df


if __name__ == '__main__':
    from dagster.cli.embedded_cli import embedded_dagster_single_pipeline_cli_main
    import sys

    embedded_dagster_single_pipeline_cli_main(sys.argv, define_pipeline())
