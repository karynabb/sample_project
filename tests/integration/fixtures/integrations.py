import pytest
from celery import Task


@pytest.fixture(autouse=True)
def task_delay_mock(mocker):
    delay_mock = mocker.patch.object(Task, "delay")
    yield delay_mock
