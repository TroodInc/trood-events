import logging
import json

import jsonschema


logger = logging.getLogger(__name__)


def validate(data, schema):
    if not isinstance(data, dict):
        try:
            data = json.loads(data)
        except ValueError:
            return False, 'Invalid JSON'

    try:
        jsonschema.validate(data, schema)
    except jsonschema.exceptions.ValidationError as error:
        return False, error.message
    
    return True, None
