#!/usr/bin/python
# -*- coding: utf-8 -*-

from itsmoredangerous import PythonSerializer

obj = {
    b'hello' : b'world',
    3 : 7,
    7.8 : 12345678901234567890,
    u'Antonín' : u'Dvořák',
    'list' : range(5),
    'dict' : {'blah' : 'monkey'},
    True : False,
    False : None,
    None : True,
}
obj['self'] = obj


s = PythonSerializer.dumps(obj)
print repr(s)
print len(s)
print PythonSerializer.loads(s)
