#!/usr/bin/python
# -*- coding: utf-8 -*-

from itsmoredangerous import (Serializer, CompressedSerializer)

serializer = CompressedSerializer()

obj = {
    b'hello' : b'world',
    3 : 7,
    7.8 : 12345678901234567890,
    u'Antonín' : u'Dvořák',
    'list' : range(5),
    'dict' : {},
}
obj['self'] = obj


s = serializer.dumps(obj)
print repr(s)
print len(s)
print serializer.loads(s)
