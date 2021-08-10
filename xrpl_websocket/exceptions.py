#!/usr/bin/env python
# coding: utf-8
class Error(Exception):
    def __init__(self, message, data):
        super(Error, self).__init__(message)

        self.message = message
        self.data = data

    def __str__(self):
        result = '[(' + self.message
        if self.data:
            result += ', ' + str(self.data)

        result += ')]'
        return result


class UnexpectedError(Error):
    pass


class ConnectionError(Error):
    pass


class NotConnectedError(ConnectionError):
    pass


class DisconnectedError(ConnectionError):
    pass


class TimeoutError(ConnectionError):
    pass


class ResponseFormatError(ConnectionError):
    pass
