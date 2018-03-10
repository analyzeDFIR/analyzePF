## -*- coding: UTF-8 -*-
## registry.py
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

class RegistryMetaclassMixin(object):
    '''
    Registry mixin class implementing registry pattern
    with Python metaprogramming. Intended to be used as
    mixin with `type`.
    '''
    _REGISTRY = None

    @classmethod
    def registry(cls):
        '''
        '''
        return dict(cls._REGISTRY)
    @classmethod
    def retrieve(cls, name):
        '''
        Args:
            name: String    => name of class to retrieve from registry
        Returns:
            Class named `name` if exists in registry, None otherwise
        Preconditions:
            name is of type String
        '''
        assert isinstance(name, str), 'Name is not of type String'
        return cls._REGISTRY.get(name)
    @classmethod
    def _add_class(cls, name, new_cls):
        '''
        Args:
            new_cls: type   => new class to add to registry
        Procedure:
            Add new class to registry if passes checks
        Preconditions:
            new_cls is subclass of DirectiveRegistry    (assumed True)
        '''
        raise NotImplementedError('_add_class not implemented for class %s'%cls.__name__)

    def __new__(cls, name, bases, attrs):
        '''
        Args:
            name: String                => name of new class
            bases: NTuple<Class>        => tuple of base classes
            attrs: Dict<String, Any>    => dictionary of type attributes
        Returns:
            Newly created directive class
        Preconditions:
            name is of type String              (assumed True)
            bases is of type NTuple<Class>      (assumed True)
            attrs is of type Dict<String, Any>  (assumed True)
        '''
        new_cls = type.__new__(cls, name, bases, attrs)
        cls._add_class(name, new_cls)
        return new_cls
