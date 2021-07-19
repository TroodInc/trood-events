REST API
========

GET /ping
---------

Required for checking connection to the event service.

response:

.. code-block:: json

    {
      "pong"
    }

status OK 200

POST /event
-----------

Required for pushing events to event service.

**Example:**

**request:**

protocol: https

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

**response:**

.. code-block:: json

    {
        "status": "OK"
    }


POST /ws
--------

Required for connecting users to event service.

**request:**

protocol: wss

.. code-block:: json

    {
    "protocol": "WS",
    "recipients": ["admin@demo.com"],
    "data": {
        "action": "SUBSCRIBE",
        "data": [{"message_type": "ui_message"}]
    }
    }

**response:**

.. code-block:: json

    {
        "status": "OK"
    }


Event schema
------------

Schema is represented in `jsonschema <https://json-schema.org/>`_

.. literalinclude:: ../schemas/event.json
   :language: json


Explanation of request fields
-----------------------------

+---------------------------+--------------------------------+-----------------------+
|**Name**                   |**Explanation**                 |**Options**            |
+---------------------------+--------------------------------+-----------------------+
|                           |                                |                       |
|"protocol"                 |Connection protocol             |HTTP,WS,QUEUE,PUSH     |
|                           |                                |                       |
+---------------------------+--------------------------------+-----------------------+
|                           |                                |                       |
|"recipients"               |Recipients of message           |Logins of system users |
|                           |                                |                       |
+---------------------------+--------------------------------+-----------------------+
|                           |                                |                       |
|"data.domain"              |Service domain                  |CUSTODIAN              |
|                           |                                |                       |
+---------------------------+--------------------------------+-----------------------+
|                           |                                |                       |
|"data.action"              |Event action                    |SUBSCRIBE,UNSUBSCRIBE, |
|                           |                                |RESET,NOTIFY           |
+---------------------------+--------------------------------+-----------------------+
|                           |                                |                       |
|"data.data"                |Event data                      |All information about  |
|                           |                                |the object             |
+---------------------------+--------------------------------+-----------------------+

