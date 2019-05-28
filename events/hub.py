import os
import importlib
import collections

from events.subscription import Subscribtion
    

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
        self.subsriber = Subscribtion()
    
    def add(self, key, ws):
        """
        Add client in storage.
        """
        self.storage[key].append(ws)
    
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

    async def process(self, key, data):
        """
        Process action.
        """
        INCOME_ACTIONS = ('SUBSCRIBE', 'UNSUBSCRIBE')
        OUTCOME_ACTIONS = ('NOTIFY', )
        # Validate
        action = data.pop('action', 'NOTIFY')
        action_data = data.pop('data')
        if action in INCOME_ACTIONS:
            action = getattr(self, action.lower())
            await action(key, action_data)
            return

        action_data = self.subsriber.check_subscriptions(key, action_data)
        if action_data:
            await self.notify(key, action_data)
    
    async def subscribe(self, key, data):
        data = self.subsriber.subscribe(key, data)
        await self.notify(key, data)
    
    async def unsubscribe(self, key, data):
        data = self.subsriber.unsubscribe(key, data)
        await self.notify(key, data)

    async def notify(self, key, data):
        """
        Send event to client.
        """
        for client in self.storage.get(key, []):
            await client.send_json(data)
