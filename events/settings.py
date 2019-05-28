import pathlib

from envparse import ConfigurationError, Env


def setup():
    env = Env(
        DEBUG=(bool, False),

        HOST=(str, '0.0.0.0'),
        PORT=(int, 8080),

        SECRET_KEY=(str, '548ab8296ff44d2f954c17d850833af1'),

        BROKER_URI=(str, 'amqp://rabbit:rabbit@rabbit:5672/'),
        ROUTING_KEY=(str, 'troodevents'),

        TROOD_AUTH_SERVICE_URL=(str, 'http://authorization:8000/'),
        SERVICE_DOMAIN=(str, 'EVENT'),
        SERVICE_AUTH_SECRET=(str, 'b1b4a229c0cb5865f67f0626dc9c184526dc6dd99f8f505b14d1c95739d523dfcfaa17534ea160364fe27e10e6c331a1c231f60be581e69fed4f5bf9c4dfdadb'),

        SENTRY_ENABLED=(bool, False),
        SENTRY_DSN=(str, 'https://b929140809d441b98f4ba197b2560d0e:8929448bcde043e48d712dbcd11d0794@sentry.tools.trood.ru/4'),
    )
    env.read_envfile(pathlib.Path.cwd() / '.env')
    settings = Settings(env)
    return settings


class Settings:
    def __init__(self, env):
        for key, item in env.schema.items():
            self._set_attr(env, key, item)
    
    def _set_attr(self, env, key, value):
        _class, default = value
        try:
            value = getattr(env, _class.__name__)(key)
        except ConfigurationError:
            value = default

        setattr(self, key, value)
