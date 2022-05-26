# isort: skip_file
# pylint: disable=unused-argument,reimported,unnecessary-ellipsis

# start_simple_metadata

from dagster import asset

@asset(
    metadata={
        "cereal_name": "Sugar Sprinkles"
    },
)

# end_simple_metadata


# start_typed_metadata

from dagster import asset, MetadataValue

@asset(
    metadata={
        "cereal_name": "Sugar Sparkles",
        "description": "Sparkly, sugary delight!",
        "path": MetadataValue.path("/sugar_sparkles"),
        "sales_dashboard_url": MetadataValue.url("http://mycoolsite.com/sugar_sparkle_sales")
    },
)

# end_typed_metadata