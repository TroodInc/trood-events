import os
import importlib
import collections
import logging

from events.subscription import Subscribtion


logger = logging.getLogger(__name__)


def setup(app):
    """
    Setup WebSocket hub.
    """
    app['hub'] = Hub(app)


class Hub:
    """
    WebSocket clients storage.
    """

    def __init__(self, app):
        self.app = app
        self.storage = collections.defaultdict(list)
        self.users = {}
        self.subsriber = Subscribtion()

    def add(self, user, ws):
        """
        Add client in storage.
        """
        key = user['login']
        logger.debug(f'Add ws connection with {key}')
        self.storage[key].append(ws)
        self.users[key] = user

    def remove(self, key):
        """
        Remove client from storage
        """
        delete_indexes = []
        for i, client in enumerate(self.storage.get(key, [])):
            if client not in self.app['websockets']:
                delete_indexes.append(i)

        for index in delete_indexes[::-1]:
            self.storage[key].pop(index)

        if self.storage.get(key) in (None, []):
            self.users.pop(key, None)

    async def process(self, key, data, client_hash):
        """
        Process action.
        """
        INCOME_ACTIONS = ('SUBSCRIBE', 'UNSUBSCRIBE', 'RESET')
        OUTCOME_ACTIONS = ('NOTIFY', )
        # Validate
        action = data.pop('action', 'NOTIFY')
        action_data = data.pop('data', {})
        if action in INCOME_ACTIONS:
            action = getattr(self.subsriber, action.lower())
            message = action(key, action_data, client_hash)
            message['hashes'] = {client_hash}
            await self.notify(key, [message])
            return

        if self.users.get(key):
            action_data = self.app['auth'].check_abac(
                self.users[key], action_data, data.pop('domain')
            )
        action_data = self.subsriber.check_subscriptions(key, action_data)
        if action_data:
            await self.notify(key, action_data)

    async def notify(self, key, data):
        """
        Send event to client.
        """
        ws_clients = self.storage.get(key, [])
        logger.debug(f'Notify ws clients {ws_clients}')
        for client in ws_clients:
            for _data in data:
                if hash(client) in _data['hashes']:
                    message = dict(_data)
                    message.pop('hashes')
                    await client.send_json(message)
