import json

async def test_ping(client):
    response = await client.get('/ping/')
    assert response.status == 200

    data = await response.json()
    assert data == 'pong'


async def test_example_event(client, headers):
    data = {'protocol': 'HTTP', 'recipients': [], 'data': {}}
    response = await client.post('/event/', json=data, headers=headers)
    assert response.status == 200
