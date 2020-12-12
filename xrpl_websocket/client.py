#!/usr/bin/env python
# coding: utf-8
import logging
import time
import json
import sys, inspect
import random, uuid
from multiprocessing import Queue
from threading import Thread, Event, Timer

import websocket

from .exceptions import ResponseFormatError, TimeoutError

class Client(Thread):
    """
    Higher level of APIs are provided.
    The interface is like JavaScript WebSocket object.
    """
    def __init__(self, server=None, timeout=None, log_level=None, *args, **kwargs):
        """
        Args:
            server: rippled node url.
            timeout: connection timeout seconds
            log_level: loggin level
            on_open: callable object which is called at opening websocket.
            on_reconnect: callable object which is called at reconnecting
            on_error: callable object which is called when we get error.
            on_close: callable object which is called when closed the connection.
            on_transaction: callback object which is called when we recieve transacion
            on_ledger: callback object which is called when we recieve ledger close
            on_validation: callback object by the validations stream when the server receives a validation message
            on_manifest: callback object sent by the manifests stream when the server receives a manifest.
        """

        # assing any callback method
        available_callbacks = [
            'on_open','on_reconnect', 'on_close','on_error',
            'on_transaction', 'on_validation', 'on_ledger',
            'on_manifest'
       ]

        for key,value in kwargs.items():
            if(key in available_callbacks):
                setattr(self, key, value)

        self.socket = None
        self.server = server if server else 'wss://xrpl.ws'
        self.responseEvents = dict()
        self.q = Queue()

        # ledger status
        self._ledgerVersion = None
        self._fee_base = None
        self._fee_ref = None

        # Connection Handling Attributes
        self.connected = Event()
        self.disconnect_called = Event()
        self.reconnect_required = Event()
        self.reconnect_interval = 10
        self.paused = Event()

        # Setup Timer attributes
        # Tracks API Connection & Responses
        self.ping_timer = None
        self.ping_interval = 10

        # Tracks Websocket Connection
        self.connection_timer = None
        self.connection_timeout = timeout if timeout else 30
        self.response_timeout = timeout if timeout else 30

        # Tracks responses from send_ping()
        self.pong_timer = None
        self.pong_received = False
        self.pong_timeout = 30

        # Logging stuff
        self.log = logging.getLogger(self.__module__)
        logging.basicConfig(stream=sys.stdout, format="[%(filename)s:%(lineno)s - %(funcName)10s() : %(message)s")
        if log_level == logging.DEBUG:
            websocket.enableTrace(True)
        self.log.setLevel(level=log_level if log_level else logging.ERROR)

        # Call init of Thread and pass remaining args and kwargs
        Thread.__init__(self)
        self.daemon = False

    def connect(self, nowait=True):
        """
        Simulate self.start(), run the main thread

        :return:
        """
        self.start()

        if not nowait:
            return self.connected.wait()

    def disconnect(self):
        """
        Disconnects from the websocket connection and joins the Thread.

        :return:
        """
        self.log.debug("Disconnecting from API..")
        self.reconnect_required.clear()
        self.disconnect_called.set()
        if self.socket:
            self.socket.close()

        # stop timers
        self._stop_timers()

        self.join(timeout=1)

    def reconnect(self):
        """
        Issues a reconnection by setting the reconnect_required event.

        :return:
        """
        # Reconnect attempt at self.reconnect_interval
        self.log.debug("Initiation reconnect sequence..")
        self.connected.clear()
        self.reconnect_required.set()
        if self.socket:
            self.socket.close()

    def _connect(self):
        """
        Creates a websocket connection.

        :return:
        """
        self.log.debug("Initializing Connection..")
        self.socket = websocket.WebSocketApp(
            self.server,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )

        self.log.debug("Starting Connection..")
        self.socket.run_forever()

        while self.reconnect_required.is_set():
            if not self.disconnect_called.is_set():
                self.log.info("Attempting to connect again in %s seconds."
                              % self.reconnect_interval)
                self.state = "unavailable"
                time.sleep(self.reconnect_interval)

                # We need to set this flag since closing the socket will
                # set it to False
                self.socket.keep_running = True
                self.socket.run_forever()

    def run(self):
        """
        Main method of Thread.

        :return:
        """
        self.log.debug("Starting up..")
        self._connect()

    def _on_message(self, message):
        """
        Handles and passes received data to the appropriate handlers.

        :return:
        """

        # ignore income messages if we are disconnecting
        if self.disconnect_called.is_set():
            return


        raw, received_at = message, time.time()
        self.log.debug("Received new message %s at %s", raw, received_at)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Something wrong with this data, log and discard
            return

        if isinstance(data, dict):
            # This is a valid message
            self._data_handler(data, received_at)

        # We've received data, reset timers
        self._start_timers()

    def _on_close(self, *args):
        self.log.info("Connection closed")
        self.connected.clear()
        self._stop_timers()

        self._callback('on_close')

    def _on_open(self):
        self.log.info("Connection opened")
        self.connected.set()
        self.send_ping()
        self._subscribe_ledger()
        self._start_timers()
        if self.reconnect_required.is_set():
            self.log.info("Connection reconnected.")

        self._callback('on_open')

    def _on_error(self, error):
        self.log.info("Connection Error - %s", error)

        # ignore errors if we are disconnecting
        if self.disconnect_called.is_set():
            return

        self.reconnect_required.set()
        self.connected.clear()

        self._callback('on_error', error)

    def _subscribe_ledger(self):
        """
        Subscribe to the ledger close after success connect.

        :return:
        """
        self.log.debug("Subscribe to ledger changes...")
        self.socket.send(json.dumps(dict(command='subscribe', id=1, streams=['ledger'])))

    def _stop_timers(self):
        """
        Stops ping, pong and connection timers.

        :return:
        """
        if self.ping_timer:
            self.ping_timer.cancel()

        if self.connection_timer:
            self.connection_timer.cancel()

        if self.pong_timer:
            self.pong_timer.cancel()
        self.log.debug("Timers stopped.")

    def _start_timers(self):
        """
        Resets and starts timers for API data and connection.

        :return:
        """
        self.log.debug("Resetting timers..")
        self._stop_timers()

        # Sends a ping at ping_interval to see if API still responding
        self.ping_timer = Timer(self.ping_interval, self.send_ping)
        self.ping_timer.start()

        # Automatically reconnect if we did not receive data
        self.connection_timer = Timer(self.connection_timeout,
                                      self._connection_timed_out)
        self.connection_timer.start()

    def send_ping(self):
        """
        Sends a ping message to the API and starts pong timers.

        :return:
        """
        self.log.debug("Sending ping to API..")
        self.socket.send(json.dumps(dict(command='ping', id='ping')))
        self.pong_timer = Timer(self.pong_timeout, self._check_pong)
        self.pong_timer.start()

    def _check_pong(self):
        """
        Checks if a Pong message was received.

       :return:
        """
        self.pong_timer.cancel()
        if self.pong_received:
            self.log.debug("Pong received in time.")
            self.pong_received = False
        else:
            # reconnect
            self.log.debug("Pong not received in time."
                           "Issuing reconnect..")
            self.reconnect()

    def send(self, payload=None, **kwargs):
        """
        Sends the given Payload to the API via the websocket connection.

        :param payload:
        :param kwargs: payload parameters as key=value pairs
        :return:
        """

        if payload:
            _payload = payload
        else:
            _payload = kwargs

        if not 'id' in _payload:
            _payload['id'] = str(uuid.uuid4())


        self.log.debug("Sending payload to API: %s", payload)

        try:
            self.socket.send(json.dumps(_payload))
        except websocket.WebSocketConnectionClosedException:
            self.log.error("Did not send out payload %s - client not connected. ", kwargs)

        event = Event()
        self.responseEvents[_payload.get('id')] = event

        while not event.is_set():
            emitted = event.wait(self.response_timeout)
            if(emitted):
                resp = self.q.get(1)
                if(resp['id'] == _payload['id']):
                    return resp
            else:
                raise TimeoutError('timeout on sending payload!')

    def _connection_timed_out(self):
        """
        Issues a reconnection if the connection timed out.

       :return:
        """
        self.log.debug("Timeout, Issuing reconnect..")
        self.reconnect()

    def _pause(self):
        """
        Pauses the connection.

        :return:
        """
        self.log.debug("Setting paused() Flag!")
        self.paused.set()

    def _unpause(self):
        """
        Unpauses the connection.
        Send a message up to client that he should re-subscribe to all
        channels.

        :return:
        """
        self.log.debug("Clearing paused() Flag!")
        self.paused.clear()

    def _pong_handler(self):
        """
        Handle a pong response.

        :return:
        """
        # We received a Pong response to our Ping!
        self.log.debug("Received a pong message!")
        self.pong_received = True

    def _data_handler(self, data, ts):
        """
        Distributes system messages to the appropriate handler.
        System messages include everything that arrives as a dict,

        :param data:
        :param ts:
        :return:
        """
        # Unpack the data
        event = data.get('type')

        # if data is reponse to send command
        if event == 'response':
            if not data.get('id'):
                raise ResponseFormatError('valid id not found in response', data)
            if(data.get('id') == 'ping'):
                self._pong_handler()
            else:
                self._response_handler(data, ts)

        elif event == 'ledgerClosed':
            self._ledger_handler(data, ts)
        elif event == 'transaction':
            self._callback('on_transaction', data)
        elif event == 'validationReceived':
            self._callback('on_validation', data)
        elif event == 'manifestReceived':
            self._callback('on_manifest', data)
        elif not event or data.get('error'):
            # Error handling
            # Todo: Should be handle the error
            self.log.error('error', data.error, data.error_message, data)
        else:
            self.log.error("Unhandled event: %s, data: %s", event, data)

    def _ledger_handler(self, data, ts):
        """Save ledger state
        :param data:
        :param ts:
        :return:
        """
        self._ledgerVersion = data.get('ledger_index')
        self._fee_base = data.get('fee_base')
        self._fee_ref = data.get('fee_ref')

        # emit callback
        self._callback('on_ledger', data)

    def _response_handler(self, data, ts):
        """Handles responses from socket
        :param data:
        :param ts:
        :return:
        """
        event = self.responseEvents.pop(data.get('id'), None)
        if(event):
            self.q.put(data)
            event.set()

    def _callback(self, callback, *args):
        """Emit a callback in a thread
        :param callback:
        :param *args:
        :return:
        """
        if callback:
            try:
                _callback = getattr(self, callback, None)
                if _callback is not None and callable(_callback):
                    t = Thread(target=_callback, args=args)
                    t.setDaemon(True)
                    t.start()
            except Exception as e:
                self.log.error("error from callback {}: {}".format(_callback, e))
