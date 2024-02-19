{% snapshot orders_snapshot %}

{{
    config(
      target_schema='snapshots',
      strategy='check',
      unique_key='name',
      check_cols=['name'],
    )
}}

select * from {{ ref("sort_by_calories") }}

{% endsnapshot %}