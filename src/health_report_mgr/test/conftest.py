import pytest


@pytest.fixture(autouse=True)
def set_environment_variables(monkeypatch):
    monkeypatch.setenv('MASTER_DB', 'master_db')
