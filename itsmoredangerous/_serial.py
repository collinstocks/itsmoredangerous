from cStringIO import StringIO
from gzip import GzipFile
import struct
from zlib import compress as zcompress, decompress as zdecompress

from ._utils import Enum, Object
from ._smaz import compress as scompress, decompress as sdecompress



def uint64_enc (f, num):
    f.write(struct.pack('!Q', num))


def uint64_dec (f):
    return struct.unpack('!Q', f.read(8))[0]


def double_enc (f, num):
    f.write(struct.pack('!d', num))


def double_dec (f):
    return struct.unpack('!d', f.read(8))[0]


def uintvar_enc (f, num):
    if num < 0: raise ValueError('num < 0 not unsigned')
    ret = []
    while True:
        n = num & 0x7f
        num >>= 7
        if num == 0:
            ret.append(n)
            break
        ret.append(n | 0x80)
        num -= 1
    f.write(''.join(chr(x) for x in ret))


def uintvar_dec (f):
    num = 0
    mag = 0
    i = 0
    while True:
        i += 1
        n = ord(f.read(1))
        num += n << mag
        if n & 0x80 == 0:
            break
        mag += 7
    return num


def bytes_enc (f, s):
    uintvar_enc(f, len(s))
    f.write(s)


def bytes_dec (f):
    length = uintvar_dec(f)
    return f.read(length)



def try_compress (s):
    ss = scompress(s, check_ascii=False)
    zs = zcompress(s)
    if len(ss) < min(len(s), len(zs)):
        return 's', ss
    if len(zs) < min(len(s), len(ss)):
        return 'z', zs
    return '', s



types = Enum(
    'NONE',
    'TRUE',
    'FALSE',
    'CYCLE',
    'INTp',
    'INTn',
    'FLOAT',
    'BYTES',
    'sBYTES',
    'zBYTES',
    'UNICODE',
    'sUNICODE',
    'zUNICODE',
    'LIST',
    'OBJ',
)


def _encode (f, data, objmap):
    if data in (None, True, False):
        obj_id = (data, len(objmap))  # New unique object id.
    else:
        obj_id = id(data)
    cycle = obj_id in objmap

    if not cycle:
        objmap[obj_id] = len(objmap)

    if data is None:
        uintvar_enc(f, types.NONE)

    elif data is True:
        uintvar_enc(f, types.TRUE)

    elif data is False:
        uintvar_enc(f, types.FALSE)

    elif cycle:
        uintvar_enc(f, types.CYCLE)
        uintvar_enc(f, objmap[obj_id])

    elif isinstance(data, int) or isinstance(data, long):
        if data >= 0:
            uintvar_enc(f, types.INTp)
            uintvar_enc(f, data)
        else:
            uintvar_enc(f, types.INTn)
            uintvar_enc(f, -data)

    elif isinstance(data, float):
        uintvar_enc(f, types.FLOAT)
        double_enc(f, data)

    elif isinstance(data, type(b'')):
        zmethod, data = try_compress(data)
        if zmethod == '':
            uintvar_enc(f, types.BYTES)
        elif zmethod == 's':
            uintvar_enc(f, types.sBYTES)
        elif zmethod == 'z':
            uintvar_enc(f, types.zBYTES)
        bytes_enc(f, data)

    elif isinstance(data, type(u'')):
        data = data.encode('utf_8')
        zmethod, data = try_compress(data)
        if zmethod == '':
            uintvar_enc(f, types.UNICODE)
        elif zmethod == 's':
            uintvar_enc(f, types.sUNICODE)
        elif zmethod == 'z':
            uintvar_enc(f, types.zUNICODE)
        bytes_enc(f, data)

    elif isinstance(data, list):
        uintvar_enc(f, types.LIST)
        uintvar_enc(f, list.__len__(data))
        for val in list.__iter__(data):
            _encode(f, val, objmap)

    elif isinstance(data, dict):
        if not isinstance(data, dict):
            data = getattr(data, '__dict__')
        uintvar_enc(f, types.OBJ)
        keys = dict.keys(data)
        uintvar_enc(f, len(keys))
        for key in keys:
            _encode(f, key, objmap)
            _encode(f, dict.__getitem__(data, key), objmap)

    else:
        raise ValueError('cannot serialize type %s' % type(data))


def encode (f, data):
    _encode(f, data, {})


def _decode (f, objlist):
    objtype = uintvar_dec(f)
    ret = None

    if objtype == types.NONE:
        ret = None
    elif objtype == types.TRUE:
        ret = True
    elif objtype == types.FALSE:
        ret = False
    elif objtype == types.CYCLE:
        ret = objlist[uintvar_dec(f)]
    elif objtype == types.INTp:
        ret = uintvar_dec(f)
    elif objtype == types.INTn:
        ret = -uintvar_dec(f)
    elif objtype == types.FLOAT:
        ret = double_dec(f)
    elif objtype == types.BYTES:
        ret = bytes_dec(f)
    elif objtype == types.sBYTES:
        ret = sdecompress(bytes_dec(f))
    elif objtype == types.zBYTES:
        ret = zdecompress(bytes_dec(f))
    elif objtype == types.UNICODE:
        ret = bytes_dec(f).decode('utf_8')
    elif objtype == types.sUNICODE:
        ret = sdecompress(bytes_dec(f)).decode('utf_8')
    elif objtype == types.UNICODE:
        ret = zdecompress(bytes_dec(f)).decode('utf_8')
    elif objtype == types.LIST:
        ret = []
    elif objtype == types.OBJ:
        ret = Object()

    objlist.append(ret)

    if objtype == types.OBJ:
        length = uintvar_dec(f)
        while length:
            length -= 1
            key = _decode(f, objlist)
            ret[key] = _decode(f, objlist)

    elif objtype == types.LIST:
        length = uintvar_dec(f)
        while length:
            length -= 1
            ret.append(_decode(f, objlist))

    return ret


def decode (f):
    return _decode(f, [])




class Serializer (object):

    def dump (self, f, obj):
        encode(f, obj)

    def load (self, f):
        return decode(f)

    def dumps (self, obj):
        f = StringIO()
        self.dump(f, obj)
        return f.getvalue()

    def loads (self, s):
        f = StringIO(s)
        return self.load(f)




class CompressedSerializer (Serializer):

    def dump (self, f, obj):
        with GzipFile(fileobj=f, mode='wb') as f:
            Serializer.dump(self, f, obj)

    def load (self, f):
        with GzipFile(fileobj=f, mode='rb') as f:
            return Serializer.load(self, f)




def uintvar_test ():
    failed = []
    for i in xrange(1 << 20):
        f = StringIO()
        uintvar_enc(f, i)
        f.seek(0)
        if uintvar_dec(f) != i:
            raise ValueError('uintvar_test failed: %i' % i)
