import functools
import collections
import operator
import json

from events.aio_trood_sdk.auth_http import TroodABACEngine

def test_abac():
    domain = 'TEST'
    user = {
        'login': 'boris@blade.gunseller',
        'abac': {
            '_default_resolution': 'allow'
        }
    }

    data = [{
        'message_type': 'test_message',
        'type': 'test',
        'date': '2019-04-20T14:21:07Z',
        'data': {
            'id': 15,
            'message': 'TEST MESSAGE'
        }
    }]

    engine = TroodABACEngine(user, user['abac'], data, domain)
    engine.resolve()
    assert engine.data == data

    user['abac'][domain] = {
        'test': {
            'data_GET': [
                {
                    'result': 'disallow',
                    'rule': {
                        'sbj.login': 'boris@blade.gunseller'
                    },
                    'mask': []
                }
            ]
        }
    }

    engine = TroodABACEngine(user, user['abac'], data, domain)
    engine.resolve()
    assert engine.data == []

    user['abac'][domain] = {
        'test': {
            'data_GET': [
                {
                    'result': 'disallow',
                    'rule': {
                        'sbj.login': 'boris@blade.gunseller'
                    },
                    'mask': ['message']
                }
            ]
        }
    }

    engine = TroodABACEngine(user, user['abac'], data, domain)
    engine.resolve()
    result = [{
        'message_type': 'test_message',
        'type': 'test',
        'date': '2019-04-20T14:21:07Z',
        'data': {
            'id': 15
        }
    }]

    assert engine.data == result
