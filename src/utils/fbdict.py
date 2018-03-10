## -*- coding: UTF-8 -*-
## fbdict.py
##
## Copyright (c) 2018 Noah Rubin
## 
## Permission is hereby granted, free of charge, to any person obtaining a copy
## of this software and associated documentation files (the "Software"), to deal
## in the Software without restriction, including without limitation the rights
## to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
## copies of the Software, and to permit persons to whom the Software is
## furnished to do so, subject to the following conditions:
## 
## The above copyright notice and this permission notice shall be included in all
## copies or substantial portions of the Software.
## 
## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
## OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
## SOFTWARE.

from pprint import pformat

from src.main.exceptions import FieldBoundDictKeyError

class FieldBoundDict(object):
    '''
    Implements MutableMapping interface to mimic stdlib dict type,
    although is not subclass of MutableMapping due to metaclass
    clashing with use of custom-built metaclasses (see: `RegistryMetaclassMixin`)
    Implementation inspired by Scrapy.item.DictItem. 
    See https://github.com/scrapy/scrapy/blob/master/scrapy/item.py 
    for implementation details or reference.
    '''
    _FIELDS = None
    
    def __init__(self, *args, **kwargs):
        self._VALUES = dict()
        if len(args) > 0:
            for key, value in zip(self.keys, args):
                self[key] = value
        if len(kwargs) > 0:
            for key, value in kwargs.items():
                if key in self._FIELDS:
                    self[key] = value
    def __getitem__(self, key):
        if key in self._FIELDS:
            return self._VALUES.get(key)
        else:
            raise FieldBoundDictKeyError(None, classname=type(self).__name__, fieldname=key)
    def __setitem__(self, key, value):
        if key in self._FIELDS:
            self._VALUES[key] = value
        else:
            raise FieldBoundDictKeyError(None, classname=type(self).__name__, fieldname=key)
    def __delitem__(self, key):
        if key in self._FIELDS:
            try:
                del self._VALUES[key]
            except:
                pass
        else:
            raise FieldBoundDictKeyError(None, classname=type(self).__name__, fieldname=key)
    def __getattr__(self, name):
        if name in self._FIELDS:
            return self.__getitem__(name)
        else:
            raise AttributeError('%s does not contain the attribute %s'%(type(self).__name__, name))
    def __setattr__(self, name, value):
        if name in self._FIELDS:
            self.__setitem__(name, value)
        else:
            super(FieldBoundDict, self).__setattr__(name, value)
    def __len__(self):
        return self._VALUES.__len__()
    def __iter__(self):
        return self._VALUES.__iter__()
    def __repr__(self):
        return '%s(%s)'%(type(self).__name__, pformat(dict(self)))
    def keys(self):
        return self._FIELDS.keys()
    @property
    def iterkeys(self):
        for key in self.keys():
            yield key
    def values(self):
        return [self._VALUES.get(key) for key in self.keys()]
    @property
    def itervalues(self):
        for value in self.values():
            yield value
    def items(self):
        return list(zip(self.keys(), self.values()))
    @property
    def iteritems(self):
        for item in self.items():
            yield item
    def get(self, key, default=None):
        if key not in self._FIELDS:
            return default
        value = self[key]
        return value if value is not None else default
    def copy(self):
        return self.__class__(self)
