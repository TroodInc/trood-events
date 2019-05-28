import asyncio
import json
import os
import pathlib
import uuid

import aiohttp

from events import settings


class ExampleEvents:
    def __init__(self, handler):
        self.handler = handler
        self.server = None
        self.ws = 'ws'
        self.http = 'http'
        self.headers = {
            'Content-Type': 'application/json'
        }
        self.calls = 0

    async def login(self):
        self.server = self.http
        print('Login screen')
        # login = input('Enter login: ')
        # password = input('Enter password: ')
        login = 'admin@demo.com'
        password = 'demo'
        data = {'login': login, 'password': password}
        url = f'{self.handler.http_entrypoint}api/v1.0/login/'
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=self.headers) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    self.handler.token = result['data']['token']
                    self.handler.login = result['data']['login']
                else:
                    result = await resp.read()
                    print(result)

    def subscribe(self):
        self.calls += 1
        self.server = self.ws
        return {
            "protocol": 'WS',
            "recipients": [self.handler.login],
            "data": {
                "event": "SUBSCRIBE",
                "data": [{"xxx": "amsterdam"}]
            }
        }


class Client:

    def __init__(self, loop):
        self.settings = settings.setup()
        self.token = None
        self.login = None
        self.loop = loop
        self.ws_entrypoint = f'ws://{self.settings.HOST}:{self.settings.PORT}/ws/'
        self.http_entrypoint = self.settings.TROOD_AUTH_SERVICE_URL
        self.events = None

    async def first_start(self):
        self.events = ExampleEvents(self)
        await self.events.login()
        self.print_meta()

    @property
    def headers(self):
        return {
            'content_type': 'application/json',
            'AUTHORIZATION': f'Token {self.token}'
        }

    async def ws(self):
        async with aiohttp.ClientSession(loop=self.loop, headers=self.headers) as session:
            async with session.ws_connect(self.ws_entrypoint) as ws:
                await self.prompt_and_send(ws, 'im_alive')
                async for msg in ws:
                    print('Message received from server:', msg)
                    await self.prompt_and_send(ws)
                    break_types = (
                        aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR
                    )
                    if msg.type in break_types:
                        break

    def print_menu(self):
        print('subscribe')
        print('exit')

    def print_meta(self):
        print(f'token: {self.token}, login: {self.login}')

    async def prompt_and_send(self, ws, command=None):
        self.print_menu()
        if command is None:
            command = input('Type a command to send to the server: ')

        if command == 'exit':
            print('Exiting!')
            raise KeyboardInterrupt
        elif command == 'print_meta':
            self.print_meta()

        event = getattr(self.events, command, None)
        if event:
            message = event()
        else:
            message = command

        if self.events.server == self.events.ws or event is None:
            await ws.send_json(message)


async def main(loop):
    client = Client(loop)
    await client.first_start()
    if client.token:
        await client.ws()

if __name__ == '__main__':
    print('Type "exit" to quit')
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main(loop))
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
