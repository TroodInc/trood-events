import asyncio
import aio_pika


async def main(loop):
    connection = await aio_pika.connect_robust(
        "amqp://rabbit:rabbit@127.0.0.1:5672/", loop=loop)

    async with connection:
        routing_key = "test"

        channel = await connection.channel()

        await channel.default_exchange.publish(
            aio_pika.Message(
                body='Hello {}'.format(channel.__hash__()).encode()
            ),
            routing_key=routing_key
        )


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()
