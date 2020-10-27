import os

from dagster.core.test_utils import environ


def test_environ():
    env_var1 = "env_var1"
    env_var2 = "env_var2"
    os.environ[env_var1] = "1.0"
    with environ({env_var1: "1.1", env_var2: "2.0"}):
        assert os.environ.get(env_var1) == "1.1"
        assert os.environ.get(env_var2) == "2.0"

        with environ({env_var1: None}):
            assert os.environ.get(env_var1) is None
            assert os.environ.get(env_var2) == "2.0"

            with environ({env_var1: "1.2"}):
                assert os.environ.get(env_var1) == "1.2"
                assert os.environ.get(env_var2) == "2.0"

            assert os.environ.get(env_var1) is None
            assert os.environ.get(env_var2) == "2.0"

        assert os.environ.get(env_var1) == "1.1"
        assert os.environ.get(env_var2) == "2.0"

    assert os.environ.get(env_var1) == "1.0"
    assert os.environ.get(env_var2) is None
