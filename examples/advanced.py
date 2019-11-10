#!/usr/bin/env python
# coding: utf-8
import json
import logging

from xrpl_websocket import Client

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

        print("Get server info")
        self.get_server_info()

        print("Subscribe to ledger transactions")
        self.subscribe_transactions()


    def on_close(self):
        print("on_close")

    def get_server_info(self):
        resp = self.send(command='server_info')
        print(json.dumps(resp, indent = 4))

    def subscribe_transactions(self):
        self.send({
            'command': 'subscribe',
            'streams': ['transactions']
        })

if __name__ == "__main__":
    Example()
