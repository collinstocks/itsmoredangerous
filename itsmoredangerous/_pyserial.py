import struct
from ._utils import BitStream, Enum, Object, try_compress, decompress


class PySerializer (object):

    types = Enum(
        'BACKREF',
        'BOOL',
        'FLOAT',
        'INT',
        'LIST',
        'OBJ',  # Or None
        'STRING',
        'TUPLE',
    )

    backrefable = (
        types.FLOAT,
        types.LIST,
        types.OBJ,
        types.STRING,
    )


    @classmethod
    def dump (cls, f, data):
        with BitStream(f, mode='w') as bs:
            cls.write(bs, {}, data)


    @classmethod
    def load (cls, f):
        with BitStream(f, mode='r') as bs:
            return cls.read(bs, [])


    @classmethod
    def write (cls, bs, obj_map, data):
        data_id = cls.idOf(data)
        if data_id in obj_map:
            cls.type_enc(bs, cls.types.BACKREF)
            cls.uint_enc(bs, obj_map[data_id])
            return
        typ = cls.typeOf(data)
        cls.type_enc(bs, typ)
        if typ in cls.backrefable and data is not None:
            obj_map[data_id] = len(obj_map)

        if typ == cls.types.BOOL:
            bs.write(chr(data), bits=1)
        elif typ == cls.types.FLOAT:
            cls.double_enc(bs, data)
        elif typ == cls.types.INT:
            cls.int_enc(bs, data)
        elif typ == cls.types.LIST:
            cls.uint_enc(bs, list.__len__(data))
            for val in list.__iter__(data):
                cls.write(bs, obj_map, val)
        elif typ == cls.types.OBJ:
            if data is None:
                bs.write(chr(0), bits=1)
                return
            else:
                bs.write(chr(1), bits=1)
            keys = dict.keys(data)
            cls.uint_enc(bs, len(keys))
            for key in keys:
                cls.write(bs, obj_map, key)
                cls.write(bs, obj_map, dict.__getitem__(data, key))
        elif typ == cls.types.STRING:
            cls.string_enc(bs, data)
        elif typ == cls.types.TUPLE:
            cls.uint_enc(bs, tuple.__len__(data))
            for val in tuple.__iter__(data):
                cls.write(bs, obj_map, val)


    @classmethod
    def read (cls, bs, obj_list):
        typ = cls.type_dec(bs)
        if typ == cls.types.BACKREF:
            return obj_list[cls.uint_dec(bs)]

        if typ == cls.types.BOOL:
            return bool(ord(bs.read(bits=1)))
        if typ == cls.types.FLOAT:
            val = cls.double_dec(bs)
            obj_list.append(val)
            return val
        if typ == cls.types.INT:
            return cls.int_dec(bs)
        if typ == cls.types.LIST:
            val = []
            obj_list.append(val)
            length = cls.uint_dec(bs)
            while length:
                length -= 1
                val.append(cls.read(bs, obj_list))
            return val
        if typ == cls.types.OBJ:
            if ord(bs.read(bits=1)) == 0:
                return None
            val = Object()
            obj_list.append(val)
            length = cls.uint_dec(bs)
            while length:
                length -= 1
                key = cls.read(bs, obj_list)
                val[key] = cls.read(bs, obj_list)
            return val
        if typ == cls.types.STRING:
            val = cls.string_dec(bs)
            obj_list.append(val)
            return val
        if typ == cls.types.TUPLE:
            contents = []
            length = cls.uint_dec(bs)
            while length:
                length -= 1
                contents.append(cls.read(bs, obj_list))
            return tuple(contents)


    @classmethod
    def typeOf (cls, obj):
        if isinstance(obj, bool):
            return cls.types.BOOL
        if isinstance(obj, float):
            return cls.types.FLOAT
        if isinstance(obj, int) or isinstance(obj, long):
            return cls.types.INT
        if isinstance(obj, list):
            return cls.types.LIST
        if isinstance(obj, dict) or obj is None:
            return cls.types.OBJ
        if isinstance(obj, type(b'')) or isinstance(obj, type(u'')):
            return cls.types.STRING
        if isinstance(obj, tuple):
            return cls.types.TUPLE
        raise ValueError('invalid type %r' % type(obj))

    @classmethod
    def idOf (cls, obj):
        if isinstance(obj, float):
            return 'float', obj
        if isinstance(obj, type(b'')):
            return 'bytes', obj
        if isinstance(obj, type(u'')):
            return 'unicode', obj
        return id(obj)

    @classmethod
    def type_enc (cls, bs, t):
        bs.write(chr(t), bits=3)

    @classmethod
    def type_dec (cls, bs):
        return ord(bs.read(bits=3))

    @classmethod
    def double_enc (cls, bs, num):
        bs.write(struct.pack('<d', num))

    @classmethod
    def double_dec (cls, bs):
        return struct.unpack('<d', bs.read(8))[0]

    @classmethod
    def uint_enc (cls, bs, num):
        if num < 16:
            bs.write(chr(0), bits=1)
            bs.write(chr(num), bits=4)
            return
        bs.write(chr(1), bits=1)
        num -= 16
        while True:
            n = num & 0x7f
            num >>= 7
            if num == 0:
                bs.write(chr(n))
                return
            bs.write(chr(n | 0x80))
            num -= 1

    @classmethod
    def uint_dec (cls, bs):
        if not ord(bs.read(bits=1)):
            return ord(bs.read(bits=4))
        num = 16
        mag = 0
        while True:
            n = ord(bs.read(bytes=1))
            num += n << mag
            if n & 0x80 == 0:
                return num
            mag += 7

    @classmethod
    def int_enc (cls, bs, num):
        if num < 0:
            bs.write(chr(1), bits=1)
            cls.uint_enc(bs, -num - 1)
            return
        bs.write(chr(0), bits=1)
        cls.uint_enc(bs, num)

    @classmethod
    def int_dec (cls, bs):
        if ord(bs.read(bits=1)):
            return -cls.uint_dec(bs) - 1
        return cls.uint_dec(bs)

    @classmethod
    def bytes_enc (cls, bs, s):
        cls.uint_enc(bs, len(s))
        bs.write(s)

    @classmethod
    def bytes_dec (cls, bs):
        length = cls.uint_dec(bs)
        return bs.read(bytes=length)

    @classmethod
    def string_enc (cls, bs, s):
        u = False
        if isinstance(s, type(u'')):
            u = True
            s = s.encode('utf_8')
        bs.write(chr(u), bits=1)
        zmethod, s = try_compress(s)
        bs.write(chr(zmethod), bits=2)
        cls.bytes_enc(bs, s)

    @classmethod
    def string_dec (cls, bs):
        u = ord(bs.read(bits=1))
        zmethod = ord(bs.read(bits=2))
        s = cls.bytes_dec(bs)
        s = decompress(zmethod, s)
        if u:
            s = s.decode('utf_8')
        return s
