select count(*) as count_star from {{ ref('customers') }}
