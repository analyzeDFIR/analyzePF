# -*- coding: UTF8 -*-
# models.py
# Noah Rubin
# 11/20/2017

from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, Index, text
from sqlalchemy.schema import UniqueConstraint, DDL
from sqlalchemy.ext.declarative import declarative_base, declared_attr

class BaseTableTemplate(object):
    '''
    '''
    @declared_attr
    def __tablename__(cls):
        return str(cls.__name__.lower())

    @staticmethod
    def _notnone(value):
        return str(value) if value is not None else 'None'
    def populate_fields(self, data_dict, overwrite=True):
        '''
        Args:
            data_dict: Dict<String, Any>    => dict containing data to map to fields
            overwrite: Boolean              => whether to overwrite values of current instance
        Procedure:
            Populate attributes of this instance with values from data_dict
            where each key in data_dict maps a value to an attribute.
            For example, to populate id and created_at, data_dict would be:
            {
                'id': <Integer>,
                'created_at': <DateTime>
            }
        '''
        assert isinstance(data_dict, dict) and all((isinstance(key, str) for key in data_dict)), 'Data_dict is not of type Dict<String, Any>'
        for key in data_dict:
            if hasattr(self, key) and (getattr(self, key) is None or overwrite):
                setattr(self, key, data_dict[key])
        return self

class ViewMixin(object):
    '''
    Mixin for (materialized) views
    '''
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

class ConcreteTableMixin(ViewMixin):
    '''
    Mixin class for (non-view) tables
    '''
    id          = Column(BigInteger, primary_key=True)
    created_at  = Column(TIMESTAMP(timezone=True), server_default=TimestampDefaultExpression(), index=True)

BaseTable = declarative_base(cls=BaseTableTemplate)
