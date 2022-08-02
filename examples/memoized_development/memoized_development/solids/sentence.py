from memoized_development.solids.solid_utils import get_hash_for_file

from dagster._legacy import InputDefinition, solid


@solid(
    version=get_hash_for_file(__file__),
    input_defs=[InputDefinition("dog_breed"), InputDefinition("tree_species")],
)
def emit_sentence(dog_breed, tree_species):
    return f"{dog_breed} is a breed of dog, while {tree_species} is a species of tree."
