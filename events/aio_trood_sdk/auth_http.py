import uuid
import json
import logging
import hashlib
import hmac
import base64

from aiohttp import ClientSession

logger = logging.getLogger(__name__)


class Client:

    def __init__(self, host):
        self.host = host

    @staticmethod
    def get_service_token(domain, secret):
        key = hashlib.sha1(b'trood.signer' + secret.encode('utf-8')).digest()
        signature = hmac.new(key, msg=domain.encode('utf-8'), digestmod=hashlib.sha1).digest()
        signature = base64.urlsafe_b64encode(signature).strip(b'=')
        return f'Service {domain}:{signature.decode("utf-8")}'

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

        return data

    async def verify_token(self, headers):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': headers.get('Authorization', '')
        }
        url = f'{self.host}api/v1.0/verify-token/'
        async with ClientSession() as session:
            response = await session.post(url, headers=headers)
            data = await response.json()
            if response.status != 200:
                logger.debug(response.status)
                logger.info(await response.text())

        return data
