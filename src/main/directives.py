# -*- coding: UTF-8 -*-
# directives.py
# Noah Rubin
# 01/31/2018

from src.utils.registry import RegistryMetaclassMixin 

class DirectiveRegistry(RegistryMetaclassMixin, type):
    '''
    Directive registry metaclass to store registered directives
    available to command line interface in `src.main.cli`.
    '''
    _REGISTRY = dict()

    @classmethod
    def _add_class(cls, name, new_cls):
        '''
        @RegistryMetaclassMixin._add_class
        '''
        if cls.retrieve(name) is not None or name == 'BaseDirective':
            return False
        if not hasattr(new_cls, '_KEY') or new_cls._KEY is None:
            return False
        if not hasattr(new_cls, 'run_directive') or not callable(new_cls.run_directive):
            return False
        cls._REGISTRY.update({new_cls._KEY: new_cls})
        return True

class BaseDirective(object, metaclass=DirectiveRegistry):
    '''
    Base class for creating new directives. This
    class is not included in the registry of directives
    exposed to the command line interface and should not
    be referenced outside of this module unless type checking
    a directive class.
    '''
    _KEY = None

    #TODO: implement directive base class
    pass

class ParseCSVDirective(BaseDirective):
    '''
    '''
    _KEY = 'PARSE_CSV'

class ParseBODYDirective(BaseDirective):
    '''
    '''
    _KEY = 'PARSE_BODY'

class ParseJSONDirective(BaseDirective):
    '''
    '''
    _KEY = 'PARSE_JSON'

class ParseDBDirective(BaseDirective):
    '''
    '''
    _KEY = 'PARSE_DB'
