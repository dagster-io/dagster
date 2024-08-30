import dagster as dg

# Define partitions for regions and product categories
regions = dg.StaticPartitionsDefinition(["North", "South", "East", "West"])
product_categories = dg.StaticPartitionsDefinition(["Electronics", "Clothing", "Home", "Sports"])

# Create a multi-dimensional partition definition
sales_partitions = dg.MultiPartitionsDefinition(
    {
        "region": regions,
        "category": product_categories,
    }
)

@dg.asset(partitions_def=sales_partitions)
def sales_data(context: dg.AssetExecutionContext):
    partition_key: dg.MultiPartitionKey = context.partition_key
    region = context.partition_key.keys_by_dimension["region"]
    category = context.partition_key.keys_by_dimension["category"]
    context.log.info(f"Processing sales data for {region} region, {category} category")
    
    # Process the sales data for the specific region and category
    processed_data = process_sales_data(region, category)
    
    return processed_data

def process_sales_data(region, category):
    # Implement your data processing logic here
    return f"Processed sales data for {region} region, {category} category"

# Example of how to materialize a specific partition
if __name__ == "__main__":
    result = dg.materialize(
        [sales_data],
        partition_key=dg.MultiPartitionKey({"region": "North", "category": "Electronics"})
    )
    print(result.success)