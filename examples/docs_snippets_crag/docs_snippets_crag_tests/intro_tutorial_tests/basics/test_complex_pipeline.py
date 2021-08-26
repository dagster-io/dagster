from docs_snippets_crag.intro_tutorial.basics.connecting_solids.complex_pipeline import diamond
from docs_snippets_crag.intro_tutorial.test_util import patch_cereal_requests


@patch_cereal_requests
def test_complex_graph():
    result = diamond.execute_in_process()
    assert result.success
