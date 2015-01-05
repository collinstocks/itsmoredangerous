from ._crypto import StreamCipher
from cStringIO import StringIO


def encrypt (key, namespace, s):
    f = StringIO()
    StreamCipher(key, namespace, f, mode='w').write(s)
    return f.getvalue()


def decrypt (key, namespace, s):
    f = StringIO(s)
    return StreamCipher(key, namespace, f, mode='r').read()
