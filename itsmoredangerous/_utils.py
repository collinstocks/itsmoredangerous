from datetime import datetime, timedelta
from bitarray import bitarray

from zlib import compress as zcompress, decompress as zdecompress
from ._smaz import compress as scompress, decompress as sdecompress



class Object (dict):
    def __init__ (self, *args, **kwds):
        dict.__init__(self, *args, **kwds)
        self.__dict__ = self
    def __setstate__ (self, state):
        self.__dict__ = state



class Enum (Object):
    def __init__ (self, *args, **kwds):
        Object.__init__(self, zip(args, range(len(args))), **kwds)
    def invert (self, num):
        return [k for k in self if self[k] == num]



class BitStream (object):

    def __init__ (self, f, mode='r'):
        if mode not in ['r', 'w']:
            raise ValueError('mode must be "r" or "w"')
        self.__f = f
        self.__buf = bitarray(endian='little')
        self.__entered = None
        self.__mode = mode

    def __enter__ (self):
        if self.__entered is None:
            self.__entered = True
        else:
            raise RuntimeError('Cannot use same BitStream twice')
        if self.__mode == 'r':
            self.read = self.__read
        else:
            self.write = self.__write
        return self

    def __exit__ (self, *ignored):
        if self.__mode == 'w':
            self.__f.write(self.__buf.tobytes())
        self.read = self.write = self.__error
        self.__entered = False

    def __write (self, s, bits=None):
        if bits is None:
            bits = len(s) << 3
        total_bits = self.__buf.length() + bits
        self.__buf.frombytes(s)
        del self.__buf[total_bits:]
        to_write = self.__buf.length() >> 3
        self.__f.write(self.__buf.tobytes()[:to_write])
        del self.__buf[:to_write << 3]

    def __read (self, bytes=0, bits=0):
        bits += bytes << 3
        to_read = (bits - self.__buf.length() + 7) >> 3 # round up
        self.__buf.frombytes(self.__f.read(to_read))
        ret = self.__buf[:bits].tobytes()
        del self.__buf[:bits]
        return ret

    def __error (self, *args, **kwds):
        if not self.__entered:
            message = 'You must only use BitStream inside a "with" statement'
        elif self.__mode == 'r':
            message = 'This BitStream is read-only'
        else:
            message = 'This BitStream is write-only'
        raise RuntimeError(message)

    read = write = __error



def try_compress (s):
    ss = scompress(s, check_ascii=False)
    zs = zcompress(s)
    if len(ss) < min(len(s), len(zs)):
        return 1, ss
    if len(zs) < min(len(s), len(ss)):
        return 2, zs
    return 0, s



def decompress (zmethod, s):
    if zmethod == 2:
        return zdecompress(s)
    elif zmethod == 1:
        return sdecompress(s)
    return s



def now ():
    return int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())
