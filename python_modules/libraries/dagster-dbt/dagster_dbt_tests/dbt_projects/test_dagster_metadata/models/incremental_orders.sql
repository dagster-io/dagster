{{
  config(
    materialized='incremental',
    unique_key='order_id',
    incremental_strategy='append',
  )
}}

select order_id from {{ ref('orders') }}
