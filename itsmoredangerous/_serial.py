from cStringIO import StringIO
import json

from ._pyserial import PySerializer as _PySerializer



class Serializer (object):

    @classmethod
    def dump (cls, f, obj):
        raise NotImplementedError

    @classmethod
    def load (cls, f, obj):
        raise NotImplementedError

    @classmethod
    def dumps (cls, obj):
        f = StringIO()
        cls.dump(f, obj)
        return f.getvalue()

    @classmethod
    def loads (cls, s):
        f = StringIO(s)
        return cls.load(f)



class PythonSerializer (Serializer):

    @classmethod
    def dump (cls, f, obj):
        _PySerializer.dump(f, obj)

    @classmethod
    def load (cls, f):
        return _PySerializer.load(f)



class JSONSerializer (Serializer):

    @classmethod
    def dump (self, f, obj):
        json.dump(obj, f, separators=(',', ':'))

    @classmethod
    def load (self, f):
        return json.load(f)




def uintvar_test ():
    failed = []
    for i in xrange(1 << 20):
        f = StringIO()
        uintvar_enc(f, i)
        f.seek(0)
        if uintvar_dec(f) != i:
            raise ValueError('uintvar_test failed: %i' % i)
