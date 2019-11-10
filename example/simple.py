#!/usr/bin/env python
# coding: utf-8
import sys
import json
from os import path

sys.path.append(path.join(path.dirname(__file__), '..'))

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






