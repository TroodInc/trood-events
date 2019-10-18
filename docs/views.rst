Views module
============

Event schema
------------

Schema is represented in `jsonschema <https://json-schema.org/>`_

.. literalinclude:: ../schemas/event.json
   :language: json

Examples
--------

.. code-block:: json
    
    {
        "protocol": "WS",
        "recipients": ["admin@demo.com"],
        "data": {
            "action": "SUBSCRIBE",
            "data": [{"message_type": "ui_message"}]
        }
    }

.. code-block:: json
    
    {
        "protocol": "WS",
        "recipients": ["admin@demo.com"],
        "data": {
            "domain": "CUSTODIAN",
            "action": "NOTIFY",
            "data": [{
                "message_type": "ui_message",
                "type": "BO name",
                "date": "2019-04-20T14:21:07Z",
                "data": {"message": "TEST MESSAGE"}
            }]
        }
    }

Functions
----------------
.. automodule:: events.views
    :members:
