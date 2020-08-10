from docs_snippets.overview.configuration.configured_named_solid_example import run_pipeline


def test_stats_pipeline():
    result = run_pipeline()
    sample_variance = result.result_for_solid('sample_variance').output_value()
    population_variance = result.result_for_solid('population_variance').output_value()

    assert round(sample_variance) == round(13.490737563232)
    assert round(population_variance) == round(1.7380544678845)
