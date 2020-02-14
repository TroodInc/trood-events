import asyncio
import json
import logging

from aiohttp import ClientSession

import aio_pika

from events.validators import validate


logger = logging.getLogger(__name__)


def setup(app):
    """
    Setup broker connection.
    """
    app['broker'] = Broker(app, app['settings'].BROKER_URI)

class Broker:
    """
    RabbitMQ interface.
    """
    def __init__(self, app, uri):
        self.app = app
        self.uri = uri

    async def connect(self, app):
        """
        Connect to broker.
        """
        self.connection = await aio_pika.connect_robust(
            self.uri, loop=app.loop
        )
        logger.info('Broker connection was create')

        await self.consume()

    async def shutdown(self, app):
        """
        Close broker connection.
        """
        await self.connection.close()
        logger.info('Broker connection was close')

    async def consume(self):
        """
        Consume messages from queue.
        """
        channel = await self.connection.channel()    # type: aio_pika.Channel
        # Declaring queue
        queue = await channel.declare_queue(
            self.app['settings'].ROUTING_KEY,
            # auto_delete=True
        )   # type: aio_pika.Queue

        await queue.consume(self.process_message)
    
    async def produce(self, data, routing_key=None):
        """
        Send new message in queue.
        """
        if routing_key is None:
            routing_key = self.app['settings'].ROUTING_KEY

        try:
            channel = await self.connection.channel()    # type: aio_pika.Channel
        except AttributeError:
            return False

        message = json.dumps(data).encode()
        logger.debug(message)
        await channel.default_exchange.publish(
            aio_pika.Message(body=message), routing_key=routing_key
        )
        return True
    
    async def process_message(self, message):
        """
        Process message from queue.
        """
        async with message.process():
            data = message.body
            if not isinstance(data, dict):
                data = json.loads(data)

            logger.debug(data)
            # Validate data
            is_valid = validate(data, self.app['schemas']['Event'])
            if is_valid:
                # Route to recipient
                await self.route(data)
                # await asyncio.sleep(1)
            else:
                logger.debug('Bad message.')
    
    async def route(self, data):
        """
        Route data to given protocol
        """
        if not isinstance(data, dict):
            data = json.loads(data)

        protocol = data.pop('protocol')
        protocol_handler = getattr(self, f'{protocol.lower()}_handler')
        await protocol_handler(data)
    
    async def queue_handler(self, data):
        """
        Send data to QUEUE recipients.

        Recipient it is queue ROUTING_KEY
        """
        for recipient in data['recipients']:
            await self.produce(data['data'], recipient)
    
    async def http_handler(self, data):
        """
        Send data to HTTP recipients.

        Recipient it is tuple of URL and user TOKEN
        """
        for url, token in data['recipients']:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': token
            }
            async with ClientSession(headers=headers) as session:
                response = await session.post(url, data['data'])
                data = await response.json()
                if response.status != 200:
                    logger.debug(response.status)

                logger.debug(json.dumps(data, indent=4))

    async def ws_handler(self, data):
        """
        Send data to WS recipients.

        Recipient it is user email.
        """
        for recipient in data['recipients']:
            await self.app['hub'].process(recipient, data['data'])
    
    async def push_handler(self, data):
        """
        Send data to PUSH recipients.

        Recipient it is user DEVICE_ID.

        Not implemented.
        """
        raise NotImplementedError
