{{
    config(
        meta={
            'dagster': {
                'asset_key': ['customers']
            }
        }
    )
}}
-- depends_on: {{ ref('orders') }}

select 1 from {{ ref('customers') }} where false
