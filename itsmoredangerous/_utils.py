from datetime import datetime, timedelta
from bitarray import bitarray



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



class BitStream (object):

    def __init__ (self, f):
        self.__f = f
        self.__buf = bitarray()
        self.__entered = False

    def __enter__ (self):
        self.__entered = True

    def __exit__ (self):
        self.__f.write(self.__buf.tobytes())

    def write (self, s, delta_bits=None):
        self.__buf.frombytes(s)
        for i in range(delta_bits):
            self.__buf.pop()
        flush_len = self.__buf.length() // 8
        self.__f.write(self.__buf.tobytes()[:flush_len])
        self.__buf = self.__buf[8*flush_len:]

    def read (self, bytes=0, bits=0):
        pass



def now ():
    return int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())
