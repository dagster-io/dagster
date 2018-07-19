from dagster.utils import has_context_argument


def test_has_context_variable():
    # pylint: disable=W0613

    def nope(_foo):
        pass

    def yup(context, _bar):
        pass

    assert not has_context_argument(nope)
    assert has_context_argument(yup)
    assert not has_context_argument(lambda: None)
    assert not has_context_argument(lambda bar: None)
    assert has_context_argument(lambda context: None)
    assert has_context_argument(lambda bar, context: None)
