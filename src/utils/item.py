# -*- coding: UTF8 -*-
# item.py
# Noah Rubin
# 02/01/2018
## Partial design and implementation taken from Scrapy project
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
    @staticmethod
    def _JSON_transform_to(keys, values):
        '''
        @BaseItem._transform_to
        '''
        return json_dumps({key:value for key,value in zip(keys, values)})
    @staticmethod
    def _CSV_transform_to(keys, values, sep):
        '''
        @BaseItem._transform_to
        '''
        raise NotImplementedError('to_CSV is not implemented for type %s'%cls.__name__)
    @classmethod
    def _JSON_transform_from(cls, input_json):
        '''
        @BaseItem._transform_from
        '''
        if isinstance(input_json, str):
            input_dict = json_loads(input_json)
            return cls(**{key:value for key,value in input_dict.items() if key in cls._FIELDS})
        return None
    @classmethod
    def _CSV_transform_from(cls, input_csv, sep):
        '''
        @BaseItem._transform_from
        '''
        raise NotImplementedError('from_CSV is not implemented for type %s'%cls.__name__)
    @classmethod
    def _transform_from(cls, transform, *args, **kwargs):
        '''
        Args:
            transform: Func<Any, Dict<String, Any>> => function that maps
            *args and **kwargs to type Dict<String, Any> that can be passed
            into cls.__init__.
        Returns:
            Instance of this class.  Note this function does not handle errors
            on purpose, as errors should be handled by routines using this
            functionality (aka a logger)
        Preconditions:
            transform is of type Func<Any, Dict<String, Any>>
            transform accepts all parameters passed to *args, **kwargs
        '''
        return cls(**transform(*args, **kwargs))
    @classmethod
    def from_JSON(cls, input_json):
        '''
        @BaseItem._transform_from
        '''
        return cls._transform_from(cls._JSON_transform_from, input_json)
    @classmethod
    def from_CSV(cls, input_csv, sep=','):
        '''
        @BaseItem._transform_from
        '''
        return cls._transform_from(cls._CSV_transform_from, input_csv, sep)

    def _transform_to(self, transform, *args, **kwargs):
        '''
        Args:
            transform: Func<<List<String>, List<Any>[, Any]>, Any> => function to 
            transform self.keys (List<String>), self.values (List<Any>), and any of *args, **kwargs
            into new data format
        Returns:
            Output of performing transform(self.keys, self.values).  Note this function does not
            handle errors on purpose, as errors should be handled by routines using this
            functionality (aka by a logger)
        Preconditions:
            transform is of type Func<<List<String>, List<Any>[, Any]>, Any>
        '''
        return transform(self.keys, self.values, *args, **kwargs)
    def to_JSON(self):
        '''
        @BaseItem._transform_to
        '''
        return self._transform_to(self._JSON_transform_to)
    def to_CSV(self, sep=','):
        '''
        @BaseItem._transform_to
        '''
        return self._transform_to(self._CSV_transform_to, sep)

class PrefetchItem(BaseItem):
    '''
    Class for parsing Windows prefetch files
    '''
    header              = Field(1)
    file_info           = Field(2)
    file_metrics        = Field(3)
    trace_chains        = Field(4)
    filename_strings    = Field(5)
    volumes_info        = Field(6)
