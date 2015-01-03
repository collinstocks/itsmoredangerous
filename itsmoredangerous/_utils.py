from datetime import datetime, timedelta


class Object (dict):
    def __init__ (self, *args, **kwds):
        dict.__init__(self, *args, **kwds)
        self.__dict__ = self
    def __setstate__ (self, state):
        self.__dict__ = state


class Enum (Object):
    def __init__ (self, *args, **kwds):
        Object.__init__(self, zip(args, range(len(args))), **kwds)
        self.__dict__ = self
    def __setstate__ (self, state):
        self.__dict__ = state


def now ():
    return int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())
