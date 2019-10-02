import uuid
import json
import logging
import hashlib
import hmac
import base64

from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientResponseError


from trood.contrib.django.auth.engine import TroodABACResolver as ABACResolver, TroodABACEngine as ABACEngine

logger = logging.getLogger(__name__)


class TroodABACEngine(ABACEngine):
    retrive_actions = {'data_GET'}

    def __init__(self, user, rules, data, domain, default=None):
        if default is None:
            default = 'allow'

        self.default_resolution = rules.get('_default_resolution', default)
        if self.default_resolution == 'allow':
            self.default_resolution = True
        else:
            self.default_resolution = False

        self.subject = user
        self.rules = rules.get(domain, {})
        self.context = data
        self.data = []

    def resolve(self):
        for context in self.context:
            actions = self.rules.get(context['type'])
            if actions is None and self.default_resolution:
                self.data.append(context)
                continue

            for action, rules in actions.items():
                if action not in self.retrive_actions:
                    continue

                result, filters, mask = self.check_permited(rules, self.subject, context)
                if not result:
                    continue

                if filters:
                    data = self.filter_data(context, filters)
                else:
                    data = context

                if mask:
                    [data['data'].pop(f) for f in mask]

                if data:
                    self.data.append(data)

    def check_permited(self, rules, subject, context):
        resolver = TroodABACResolver(subject=subject, context=context)
        for rule in rules:
            result, filters, mask = resolver.evaluate_rule(rule)
            if result:
                return True, filters, mask

        return False, None, None

    def filter_data(self, data, filters):
        return data


class TroodABACResolver(ABACResolver):

    def __init__(self, subject, context):
        self.data_source = {"sbj": subject, "ctx": context}

    def evaluate_rule(self, rule: dict) -> (bool, list, list):
        filters = []
        result = True
        operator = "exact"

        for operand, value in rule['rule'].items():
            if type(value) is dict:
                operator, value = list(value.items())[0]

            elif type(value) is list:
                operator = operand

            operand, value, is_filter = self.reveal(operand, value)

            if is_filter:
                filters.append(self.make_filter(operand, value))
            else:
                result, flt = getattr(self, f'operator_{operator}')(value, operand)
                if flt:
                    filters.append(flt)

        if rule['result'] == 'disallow' and not rule['mask']:
            result = not result

        return result, filters, rule['mask']

    def make_filter(self, operand: str, value):
        operator = "exact"
        if type(value) is dict:
            operator, value = list(value.items())[0]

        operand = "{}__{}".format(operand.replace(".", "__"), operator)

        return {operand: value}


class Client:

    def __init__(self, host):
        self.host = host

    @staticmethod
    def get_service_token(domain, secret):
        key = hashlib.sha1(b'trood.signer' + secret.encode('utf-8')).digest()
        signature = hmac.new(key, msg=domain.encode('utf-8'), digestmod=hashlib.sha1).digest()
        signature = base64.urlsafe_b64encode(signature).strip(b'=')
        return f'Service {domain}:{signature.decode("utf-8")}'

    @staticmethod
    def check_abac(user, data, domain):
        engine = TroodABACEngine(user, user['abac'], data, domain)
        engine.resolve()
        return engine.data

    def get_headers(self, token=None):
        headers = {'Content-Type': 'application/json'}
        if token:
            headers.update({'Authorization': token})
        return headers

    async def login(self, login, password):
        url = f'{self.host}api/v1.0/login/'
        data = {'login': login, 'password': password}
        headers = self.get_headers()
        async with ClientSession(headers=headers) as session:
            response = await session.post(url, json=data)
            if response.status != 200:
                logger.info(response.status)
                logger.info(await response.text())
                return data

            data = await response.json()
            logger.info(json.dumps(data, indent=4))

        return data

    async def verify_token(self, headers):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': headers.get('Authorization', '')
        }
        url = f'{self.host}api/v1.0/verify-token'
        async with ClientSession() as session:
            response = await session.post(url, headers=headers)
            data = await response.json()
            if response.status != 200:
                logger.debug(response.status)

            logger.debug(json.dumps(data, indent=4))

        return data
