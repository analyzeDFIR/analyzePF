## -*- coding: UTF8 -*-
## item.py
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

## see https://github.com/scrapy/scrapy/blob/master/scrapy/item.py for details

from pprint import pformat
from collections import OrderedDict
from json import dumps as json_dumps, loads as json_loads

from src.utils.fbdict import FieldBoundDict

class Field(dict):
    '''
    Field metadata container
    '''
    def __init__(self, idx, **kwargs):
        super(Field, self).__init__(**kwargs)
        self['idx'] = idx
    def __repr__(self):
        return '%s(%s)'%(type(self).__name__, pformat(dict(self)))

class ItemMeta(type):
    '''
    Metaclass of item structures.  The __new__ function hooks the creation
    of subclasses of BaseItem to attach any declared attributes, or fields,
    to the newly formed classes _FIELDS attribute.  This also implements 
    field inheritance, meaning both fields and metadata for each Field object
    are inherited.  For example, given the following parent and child classes:
    
    class ParentStructure(BaseItem):
        f0 = Field(0)
        f1 = Field(1, serializer=str)
        f2 = Field(2, ftype='JSON')

    class ChildStructure(BaseItem):
        f2 = Field(0, ftype='CSV')
        f3 = Field(1)

    type ChildStructure would have the following _FIELDS object:

    OrderedDict([
        (f0, Field(0)),
        (f1, Field(1, serializer=str)),
        (f2, Field(2, ftype='CSV')),
        (f3, Field(3))
    ])

    there are a few things to notice here:

        + ChildStructure inherits fields from ParentStructure
        + Fields in ChildStructure are reindexed to maintain linearly
          increasing index for all fields in the class hierarchy, much like in a database
        + Fields re-declared in child classes are merged with fields in parent
          classes, which is why f2.ftype was updated to 'CSV'
    '''

    def __new__(cls, name, bases, attrs):
        field_attrs = list(filter(lambda attr: isinstance(attrs[attr], Field), attrs))
        field_attrs = sorted([\
            attr for attr in attrs if isinstance(attrs.get(attr), Field)
        ], key=lambda x: attrs.get(x).get('idx'))
        if attrs.get('_FIELDS') is None and len(field_attrs) == 0:
            return super(ItemMeta, cls).__new__(cls, name, bases, attrs)
        else:
            item_bases = tuple(filter(\
                lambda base: hasattr(base, '_FIELDS') and base._FIELDS is not None, \
                bases)\
            )
            num_fields = 0
            new_fields = OrderedDict()
            new_attrs = {key:value for key,value in attrs.items() if not isinstance(value, Field)}
            for item_base in item_bases:
                for key in item_base._FIELDS:
                    if key not in new_fields:
                        new_fields[key] = Field(\
                            num_fields, \
                            **{\
                                key:value for key,value \
                                in item_base._FIELDS.get(key).items() \
                                if key != 'idx'
                            })
                        num_fields += 1
                    else:
                        new_fields.get(key).update(item_base._FIELDS.get(key))
                for key in dir(item_base):
                    attr = getattr(item_base, key)
                    if not isinstance(attr, Field) and key in attrs:
                        new_attrs[key] = attrs.get(key)
            for attr in field_attrs:
                if attr not in new_fields:
                    new_fields[attr] = Field(\
                        num_fields, \
                        **{\
                            key:value for key,value \
                            in attrs.get(attr).items() \
                            if key != 'idx'
                        })
                    num_fields += 1
                else:
                    new_fields.get(attr).update(attrs.get(attr))

            new_attrs['_FIELDS'] = new_fields
            new_cls = super(ItemMeta, cls).__new__(cls, name, bases, new_attrs)
            ## NOTE: adding class to registry disable for development for now,
            ##       currently considering whether or not holding reference to
            ##       classes for lifetime of program is useful.
            #cls._add_class(name, new_cls)
            return new_cls

class BaseItem(FieldBoundDict, metaclass=ItemMeta):
    '''
    Base item class all item types will inherit from.  For more 
    information on the registry and metaclass patterns in python, see
    https://github.com/faif/python-patterns/blob/master/behavioral/registry.py
    '''
    pass
