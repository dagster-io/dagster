SELECT
  DATE_TRUNC('day', {{ date_column }}) as date,
  SUM({{ amount_column }}) as daily_revenue
FROM {{ table_name }}
WHERE {{ date_column }} >= '{{ start_date }}'
GROUP BY DATE_TRUNC('day', {{ date_column }})
ORDER BY date
