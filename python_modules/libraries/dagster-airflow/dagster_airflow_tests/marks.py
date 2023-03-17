import pytest

requires_local_db = pytest.mark.requires_local_db  # requires airflow db (but not k8s)
requires_persistent_db = pytest.mark.requires_persistent_db  # requires persistent airflow db
requires_no_db = pytest.mark.requires_no_db  # requires no database
