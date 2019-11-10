
XRPL Websocket
==============

.. image:: https://readthedocs.org/projects/xrpl-websocket/badge/?version=latest
    :target: https://xrpl-websocket.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://badge.fury.io/py/xrpl-websocket.svg
    :target: https://badge.fury.io/py/xrpl-websocket

================
      
Websocket client for rippled with reconnecting feature, support both python 2 and 3

Installation
============

Via pip:

.. code-block:: bash

    pip install xrpl_websocket
    
Examples
========

Short-lived connection
----------------------
Simple example to send a payload and wait for response

.. code:: python

    import json

    from xrpl_websocket import Client

    if __name__ == "__main__":
        # create instance
        client = Client()

        # connect to the websocket
        client.connect(nowait=False)

        # send server info command
        resp = client.send(command='server_info')

        print("Server Info:")
        print(json.dumps(resp, indent = 4))

        # close the connection
        client.disconnect()

More advanced: Custom class
---------------------------
You can also write your own class for the connection, if you want to handle the nitty-gritty details yourself.

.. code:: python

    class Example(Client):
        def __init__(self):
            super(self.__class__, self).__init__(
                log_level=logging.ERROR,
                server="wss://rippled.xrptipbot.com"
            )

            # connect to the websocket
            self.connect()

        def on_transaction(self, data):
            print(json.dumps(data, indent = 4))

        def on_ledger(self,data):
            print('on_ledger')

        def on_open(self):
            print("Connection is open")

            print("Subscribe to ledger transactions")
            self.subscribe_transactions()


        def on_close(self):
            print("on_close")

        def subscribe_transactions(self):
            self.send({
                'command': 'subscribe',
                'streams': ['transactions']
            })


