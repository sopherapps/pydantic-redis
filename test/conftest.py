import pytest
import redislite


@pytest.fixture()
def redis_server(unused_tcp_port):
    """Sets up a fake redis server we can use for tests"""
    instance = redislite.Redis(serverconfig={"port": unused_tcp_port})
    yield f"redis://127.0.0.1:{unused_tcp_port}/0"
