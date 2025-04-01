import dagster as dg

monthly_partition = dg.MonthlyPartitionsDefinition(start_date="2024-01-01")

product_category_partition = dg.StaticPartitionsDefinition(
    ["Electronics", "Books", "Home and Garden", "Clothing"]
)
