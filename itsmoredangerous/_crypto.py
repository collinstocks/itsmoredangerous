from base64 import b64encode
from keccak import Sponge as _Sponge
import os
from textwrap import dedent


def Sponge (key, namespace, nonce='', mac=False, stream=False, rng=False):
    '''
    Returns a keyed keccak sponge object with a security level of 256 bits.
    Encodes various settings in the header to namespace the resultant sponge.

    The sponge object is initialized with a null-terminated header.
    The implementation is based on the recommendations found on
    page 20 of http://sponge.noekeon.org/CSF-0.1.pdf. The header
    itself does not contain any null characters.
    '''
    if sum([mac, stream, rng]) != 1:
        raise ValueError('choose exactly one: mac, stream, or rng')
    sponge = _Sponge(1088, 512)
    header = dedent('''\
        itsmoredangerous._crypto.Sponge
        version: 20150104
        security level: 256 bits
        key: %(key)s
        namespace: %(namespace)s
        purpose: %(purpose)s
        nonce: %(nonce)s
        library key: SFBn3NRJLHzUEs/GeUt+3GTbOVRQ7hDV
    ''' % {
        'key' : b64encode(key).rstrip('='),
        'namespace' : b64encode(namespace).rstrip('='),
        'purpose' : 'mac' if mac else
            'stream' if stream else
                'rng' if rng else 'other',
        'nonce' : b64encode(str(nonce)).rstrip('='),
    })
    sponge.absorb(header + '\0')
    return sponge


class StreamCipher (object):
    '''
    Implements a stream cipher with a security level of 256 bits.
    Uses a 128-bit random nonce. Avoid using this class to encrypt
    more than a few hundred trillion messages with the same key
    and namespace.
    '''

    def __init__ (self, key, namespace, fobj, mode='r'):
        if mode == 'r':
            nonce = fobj.read(16)
            self.write = self.__not_implemented
        elif mode == 'w':
            nonce = os.urandom(16)  # 64-bit collision resistance
            fobj.write(nonce)
            self.read = self.__not_implemented
        else:
            raise ValueError('mode must be in ("r", "w")')
        self.__sponge = Sponge(key, namespace, nonce, stream=True)
        self.__fobj = fobj

    def __crypt (self, s):
        stream = self.__sponge.squeeze(len(s))
        return ''.join(
            chr(ord(a) ^ ord(b)) for a, b in zip(s, stream)
        )

    def __not_implemented (self, *args, **kwds):
        raise NotImplementedError

    def write (self, s):
        self.__fobj.write(self.__crypt(s))

    def read (self, length=-1):
        return self.__crypt(self.__fobj.read(length))


class MAC (object):
    '''
    Implements a message authentication code with a security level of
    256 bits. If a lower security level is needed, pass the desired
    security level in bits to MAC.digest().
    '''

    def __init__ (self, key, namespace, data='')
        self.__sponge = Sponge(key, namespace, mac=True)
        self.update(data)

    def update (self, data):
        self.__sponge.absorb(data)

    def digest (self, security=256):
        if security > 256:
            raise ValueError('maximum security level is 256 bits')
        if security < 128:
            raise ValueError('minimum security level is 128 bits')
        # The number of bits returned must be twice the security level.
        return self.__sponge.squeeze(security / 4)
