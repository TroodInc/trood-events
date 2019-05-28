import pytest

from events.server import init


async def get_token(app):
    # XXX: need something better. mock for example
    result = await app['auth'].login('admin@demo.com', 'demo')
    return result['data']['token']

@pytest.fixture
def app():
    app = init([])
    return app


@pytest.fixture
def client(loop, aiohttp_client, app):
    return loop.run_until_complete(aiohttp_client(app))


@pytest.fixture
async def headers(app):
    token = await get_token(app)
    return {
        'content-type': 'application/json',
        'Authorization': f'Token {token}'
    }
