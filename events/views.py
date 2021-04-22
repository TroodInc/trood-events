import asyncio
import json
import logging

import jsonschema

from aiohttp import web, WSMsgType

from aiohttp_swagger import swagger_path

from events.validators import validate

logger = logging.getLogger(__name__)


@swagger_path("./docs/endpoint_ping.yaml")
async def ping(request):
    """
    ping - pong view
    """
    return web.json_response('event pong')


@swagger_path("./docs/endpoint_http.yaml")
async def event(request):
    """
    Init event view.
    """
    user = await request.app['auth'].verify_token(request.headers)
    if user['status'] != 'OK':
        return web.json_response({'error': 'Forbbiden'}, status=403)

    user = user['data']
    # Recieve data
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return web.json_response({'error': 'Invalid data format'}, status=400)

    is_valid, message = validate(data, request.app['schemas']['Event'])
    if is_valid:
        # Route to queue
        await request.app['broker'].produce(data)
        return web.json_response({'status': 'OK'})
    else:
        return web.json_response({'error': message}, status=400)


@swagger_path("./docs/endpoint_ws.yaml")
async def ws(request):
    """
    WebSocket connection processing

    :param request: Context injected by aiohttp framework
    """
    # TODO: find way to remove it.
    headers= {'Authorization': f'Token {request.query.get("token")}'}
    user = await request.app['auth'].verify_token(headers)
    if user['status'] != 'OK':
        logger.info(user)
        return web.json_response({'error': 'Forbbiden'}, status=403)

    user = user['data']
    logger.info(f'Connection {user["login"]} starting')
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    request.app['websockets'].add(ws)
    request.app['hub'].add(user, ws)
    try:
        async for message in ws:
            # Recieve data
            is_text = message.type == WSMsgType.TEXT
            if is_text and message.data == 'close':
                await ws.close()
            elif is_text and message.data == 'ping':
                await ws.send_json('pong')
            elif is_text:
                logger.info(message.data)
                is_valid, msg = validate(
                    message.data, request.app['schemas']['Event']
                )
                if is_valid:
                    # Route to queue
                    data = json.loads(message.data)
                    data['hash'] = hash(ws)
                    await request.app['broker'].produce(json.dumps(data))
                else:
                    await ws.send_json({'error': msg})

            elif message.type == WSMsgType.ERROR:
                exception = ws.exception()
                logger.info(f'Connection {user["login"]} closed with exception {exception}')
    finally:
        request.app['websockets'].discard(ws)
        request.app['hub'].remove(user['login'])
        logger.info(f'Connection {user["login"]} closed')

    return ws
