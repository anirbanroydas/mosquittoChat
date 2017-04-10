import pytest
from mosquittoChat.server import main as mosquittoChat_app


@pytest.fixture(scope='session')
def app():
    return mosquittoChat_app
    