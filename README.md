itsmoredangerous
================

It's More Dangerous ... so better encrypt and sign this.

Purpose
-------

This project ([itsmoredangerous][imd]) is meant to improve on and replace the
[itsdangerous][itd] Python module by enforcing a more strict security policy
without getting in the way of project developers.
Improvements include encryption, key expiration and mandatory namespacing.


Issues with itsdangerous
------------------------

* [itsdangerous][itd] protects message integrity (signing), but not confidentiality (encryption).

* [itsdangerous][itd] signed messages are readable without first checking the signature.
  This means that a project developer can accidentally use information stored in the
  message without first checking that the message is signed.

* [itsdangerous][itd] does not allow the signer of a message to determine the expiration
  date/time of that message, and instead relies on the message loader to enforce a max_age
  in the TimedSerializer and URLSafeTimedSerializer classes.

* [itsdangerous][itd] does not enforce the use of namespaces (referred to there as "salts")
  to differentiate uses of a signing key.

* [itsdangerous][itd] uses concatenation as the default method of deriving signing keys
  from a long-term key and a namespace ("salt"). This has the result that
  ```python
from itsdangerous import Signer
signed_message = Signer('-secretkey', 'salt-signer-hello-').sign('this is a message')
print Signer('-hello-signer-secretkey', 'salt-').unsign(signed_message)
  ```
  outputs 'this is a message' instead of raising a BadSignature exception. This seems to be
  for compatibility with [django][dj]. However, safety rather than compatibility should
  be the objective of a security library. Although it is reasonable for compatibility to be
  an option, the default should be the safest possible option. In this case, that means the
  signing key should be derived from the long-term key and the namespace using HMAC.

* [itsdangerous][itd] uses time.time() to get the current time. While on almost all existing
  systems this returns the same value as
  `(datetime.utcnow() - datetime(1970, 1, 1)).total_seconds()`, [it hasn't always][pybug12758].
  This would have caused timed serializers to behave incorrectly when running on computers
  in multiple different timezones. Additionally, according to the Python [time][pydoctime]
  documentation, the time module might not handle dates beyond 2038 depending on the C
  library used. This is a serious oversight.

* [itsdangerous][itd] signing keys never expire. This would be more important if messages
  were encrypted, but it is still good practice for old keys to periodically become invalid.
  An adversary who gets access to an expired access token protected by [itsdangerous][itd]
  can use a timing attack to tell if the token was ever valid. From this, they can tell that
  such-and-such user had access to such-and-such service at such-and-such time. If the signing
  keys expired every hour or so, an adversary would not be able to tell the difference between
  an old expired token and a fake token, and thus could not derive this unauthorized information
  about a user.




[itd]: https://github.com/mitsuhiko/itsdangerous
[imd]: https://github.com/collinstocks/itsmoredangerous
[dj]: https://www.djangoproject.com/
[pybug12758]: https://bugs.python.org/issue12758
[pydoctime]: https://docs.python.org/2/library/time.html
