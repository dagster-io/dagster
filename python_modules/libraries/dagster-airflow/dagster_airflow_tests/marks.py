import pytest

nettest = pytest.mark.nettest
requires_k8s = pytest.mark.requires_k8s  # requires k8s (and optionally airflow db)
requires_airflow_db = pytest.mark.requires_airflow_db  # requires airflow db (but not k8s)
