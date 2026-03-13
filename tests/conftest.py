from django.conf import settings

pytest_plugins = [
    "tests.integration.fixtures.api",
    "tests.integration.fixtures.integrations",
    "tests.integration.fixtures.models",
]


def pytest_sessionstart(session):
    settings.TEST = True
