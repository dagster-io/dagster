import re

import pytest
from dagster.utils.backcompat import rename_warning


def test_no_additional_warn_text():
    with pytest.warns(
        UserWarning,
        match=re.escape(
            '"an_old_name" is deprecated and will be removed in 0.3.0, use "a_new_name" instead.'
        ),
    ):
        rename_warning("a_new_name", "an_old_name", "0.3.0")

    with pytest.warns(
        UserWarning,
        match=re.escape(
            '"an_old_name" is deprecated and will be removed in 0.3.0, use "a_new_name" '
            "instead. Additional compelling text."
        ),
    ):
        rename_warning("a_new_name", "an_old_name", "0.3.0", "Additional compelling text.")
