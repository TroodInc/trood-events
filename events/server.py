import asyncio
import logging
import logging.handlers
import sys
import os
import weakref

import uvloop

from aiohttp import web, WSCloseCode

from aiohttp_swagger import *

from events import routes, settings, broker, schemas, hub
from events.aio_trood_sdk import auth_http


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


def init(args):
    """ Init application. """
    app_settings = settings.setup()
    if app_settings.SENTRY_ENABLED:
        import sentry_sdk
        from sentry_sdk.integrations.aiohttp import AioHttpIntegration
            
        sentry_sdk.init(
            dsn=app_settings.SENTRY_DSN, integrations=[AioHttpIntegration()]
        )

    app = web.Application()
    app['settings'] = app_settings
    app['websockets'] = weakref.WeakSet()
    app['auth'] = auth_http.Client(app_settings.TROOD_AUTH_SERVICE_URL)
    broker.setup(app)
    routes.setup(app)
    hub.setup(app)
    schemas.setup(app)

    setup_swagger(
        app,
        title="Trood events API",
        # api_base_url="http://127.0.0.1:8081/",
        api_version="1",
        contact="info@trood.ru"
    )

    return app


async def on_shutdown(app):
    """ Shutdown application. """
    for ws in set(app['websockets']):
        await ws.close(code=WSCloseCode.GOING_AWAY, message='Server shutdown')


def run(argv):
    """
    Run application.
    """
    logging.basicConfig(
        format='%(levelname)s | %(asctime)s | %(name)s:%(lineno)s | %(message)s',
        level=logging.DEBUG,
        handlers=[logging.StreamHandler()]
    )

    app = init(argv)

    app.on_startup.append(app['broker'].connect)
    app.on_cleanup.append(app['broker'].shutdown)

    app.on_shutdown.append(on_shutdown)

    web.run_app(app, host=app['settings'].HOST, port=app['settings'].PORT)


if __name__ == '__main__':
    run(sys.argv[1:])
