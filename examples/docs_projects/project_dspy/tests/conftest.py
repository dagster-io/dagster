import os


def pytest_configure(config):
    # Bypass GEMINI_API_KEY validation in config.py (the project already supports this flag)
    os.environ.setdefault("MOCK_API_CALLS", "true")
