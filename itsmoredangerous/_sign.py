from hashlib import sha384
import hmac
import os

_builtin_constant_compare = getattr(hmac, 'compare_digest', None)


def _constant_compare (correct, unknown):
    '''
    Returns the value of `correct == unknown', computed in constant time.
    The time taken is independent of the number of characters that match.

    Unfortunately, the memory management in Python may still leak some
    information about the comparison result due to, for example,
    the integer cache. For this reason, it may make sense to sign both
    inputs with the same random key and compare their signatures. This
    would prevent an adversary from controlling the value of `unknown'
    passed to this function.
    '''
    length_equal = len(correct) == len(unknown)
    if length_equal:  # Attempt to make both branches take equal time.
        result = 0
        left = correct
    else:
        result = 1
        left = unknown  # Do not allow `correct' to go out of scope.
    for L, R in zip(left, unknown):
        # If the integer cache goes up to 255, this should be constant time.
        result |= ord(L) ^ ord(R)
    return result == 0


if _builtin_constant_compare:
    _constant_compare = builtin_constant_compare


def sign (key, s):
    return hmac.HMAC(key, msg=s, digestmod=sha384).digest()


def compare_digest (correct, unknown):
    '''
    Returns the value of `correct == unknown', computed in constant time.
    The time taken is independent of the number of characters that match.

    This function prevents the Python memory manager from leaking information
    about the match by signing `correct' and `unknown' with a new randomly-
    generated key, and comparing the signatures. Since an adversary has no
    control over nor knowledge of the output signatures, they cannot use any
    information about the match leaked by the Python memory manager. This
    implementation therefore can leak no more information about the value
    of `correct' than is leaked by the signature algorithm (HMAC) about its
    input message.
    '''
    k = os.urandom(48)
    left = sign(k, correct)
    right = sign(k, unknown)
    return _constant_compare(left, right)


def check_signature (key, s, signature):
    correct = sign(key, s)
    return compare_digest(correct, signature)
