from dagster.seven import mock
from dagster.utils.backcompat import rename_warning


def test_no_additional_warn_text():
    with mock.patch('warnings.warn') as warn_mock:
        rename_warning('a_new_name', 'an_old_name', '0.3.0')
        warn_mock.assert_called_once_with(
            '"an_old_name" is deprecated and will be removed in 0.3.0, use "a_new_name" instead.',
            stacklevel=3,
        )

    with mock.patch('warnings.warn') as warn_mock:
        rename_warning('a_new_name', 'an_old_name', '0.3.0', 'Additional compelling text.')
        warn_mock.assert_called_once_with(
            (
                '"an_old_name" is deprecated and will be removed in 0.3.0, use "a_new_name" '
                'instead. Additional compelling text.'
            ),
            stacklevel=3,
        )
