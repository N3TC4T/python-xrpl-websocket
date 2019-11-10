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


class LedgerVersionError(Error):
    pass


class ConnectionError(Error):
    pass


class NotConnectedError(ConnectionError):
    pass


class DisconnectedError(ConnectionError):
    pass


class XrplNotInitializedError(ConnectionError):
    pass


class TimeoutError(ConnectionError):
    pass


class ResponseFormatError(ConnectionError):
    pass


class ValidationError(Error):
    pass


class NotFoundError(Error):
    def __init__(self):
        super(NotFoundError, self).__init__(message='Not found')


class MissingLedgerHistoryError(Error):
    def __init__(self):
        super(MissingLedgerHistoryError, self).__init__(
            message='Server is missing ledger history in the specified range')


class PendingLedgerVersionError(Error):
    def __init__(self):
        super(PendingLedgerVersionError, self).__init__(
            message='maxLedgerVersion is greater than server\'s most recent validated ledger')
