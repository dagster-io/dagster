from memoized_development.solids.solid_utils import get_hash_for_file

from dagster._legacy import solid


@solid(version=get_hash_for_file(__file__), config_schema={"tree_species": str})
def emit_tree(context):
    species = context.solid_config["tree_species"]
    return "tree", species
