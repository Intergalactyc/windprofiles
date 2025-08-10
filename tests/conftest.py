import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--api", action="store_true", help="run tests which require API keys"
    )


def pytest_runtest_setup(item):
    if "api" in item.keywords and not item.config.getvalue("api"):
        pytest.skip("need --api option to run")
