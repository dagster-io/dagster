import dagster as dg
from project_components_pdf_extraction.definitions import defs


def test_defs_load():
    assert isinstance(defs, dg.Definitions)
