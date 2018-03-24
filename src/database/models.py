## -*- coding: UTF8 -*-
## models.py
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

from datetime import datetime
import re
from sqlalchemy.orm import relationship
from sqlalchemy.types import String, Text, Integer, TIMESTAMP, BigInteger, Boolean
from sqlalchemy import Column, ForeignKey, Index, text
from sqlalchemy.schema import UniqueConstraint, CheckConstraint, DDL
from sqlalchemy.ext.declarative import declarative_base, declared_attr

from src.utils.database import TimestampDefaultExpression, create_view 

class BaseTableTemplate(object):
    '''
    Base table class
    '''
    @declared_attr
    def __tablename__(cls):
        return str(cls.__name__.lower())

    @staticmethod
    def _convert_key(key):
        '''
        Args:
            key: String => key to convert
        Returns:
            String
            key converted from camel case to snake case
            NOTE:
                Implementation taken from:
                https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case#1176023
        Preconditions:
            key is of type String
        '''
        assert isinstance(key, str), 'Key is not of type String'
        return re.sub(\
            '(.)([A-Z][a-z]+)', r'\1_\2', re.sub(\
                '([a-z0-9])([A-Z])', r'\1_\2', key\
            )\
        ).lower()
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
        Preconditions:
            data_dict is of type Dict<String, Any>
        '''
        assert hasattr(data_dict, '__getitem__') and all((isinstance(key, str) for key in data_dict)), 'Data_dict is not of type Dict<String, Any>'
        for key in data_dict:
            converted_key = self._convert_key(key)
            if hasattr(self, converted_key) and (getattr(self, converted_key) is None or overwrite):
                setattr(self, converted_key, data_dict[key])
        return self

BaseTable = declarative_base(cls=BaseTableTemplate)

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

class FileLedgerLinkedMixin(object):
    '''
    Mixin for tables linked to metadata table
    metadata table serves as accounting system for parser
    '''
    @declared_attr
    def meta_id(cls):
        return Column(BigInteger, ForeignKey('metadata.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)

class HeaderLinkedMixin(object):
    '''
    Mixin for tables linked to header table
    '''
    @declared_attr
    def header_id(cls):
        return Column(BigInteger, ForeignKey('header.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)

class FileMetricsLinkedMixin(object):
    '''
    Mixin for tables linked to filemetrics table
    '''
    @declared_attr
    def file_metrics_id(cls):
        return Column(BigInteger, ForeignKey('filemetrics.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)

class VolumesInfoLinkedMixin(object):
    '''
    Mixin for tables linked to volumesinformation table
    '''
    @declared_attr
    def volumes_info_id(cls):
        return Column(BigInteger, ForeignKey('volumesinformation.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)

class FileLedger(BaseTable, ConcreteTableMixin):
    '''
    Parsed prefetch file metadata table
    '''
    file_name               = Column(String().with_variant(Text, 'postgresql'), nullable=False)
    file_path               = Column(String().with_variant(Text, 'postgresql'), nullable=False)
    file_size               = Column(BigInteger, nullable=False)
    md5hash                 = Column(String().with_variant(Text, 'postgresql'))
    sha1hash                = Column(String().with_variant(Text, 'postgresql'))
    sha2hash                = Column(String().with_variant(Text, 'postgresql'), nullable=False)
    modify_time             = Column(TIMESTAMP(timezone=True))
    access_time             = Column(TIMESTAMP(timezone=True))
    create_time             = Column(TIMESTAMP(timezone=True))
    completed               = Column(Boolean, index=True)
    header                  = relationship('header', backref='file_ledger')

class Header(BaseTable, ConcreteTableMixin, FileLedgerLinkedMixin):
    '''
    Prefetch file header table
    '''
    version                 = Column(String().with_variant(Text, 'postgresql'), nullable=False, index=True)
    file_size               = Column(BigInteger, nullable=False)
    executable_name         = Column(String().with_variant(Text, 'postgresql'), nullable=False, index=True)
    prefetch_hash           = Column(String().with_variant(Text, 'postgresql'), nullable=False, index=True)
    file_info               = relationship('fileinformation', backref='header')
    file_metrics            = relationship('filemetric', backref='header')
    trace_chains            = relationship('tracechain', backref='header')
    volumes_info            = relationship('volumesinformation', backref='header')

class FileInformation(BaseTable, ConcreteTableMixin, HeaderLinkedMixin):
    '''
    Prefetch file information table
    '''
    section_a_offset        = Column(Integer, nullable=False)
    section_a_entries_count = Column(Integer, nullable=False)
    section_b_offset        = Column(Integer, nullable=False)
    section_b_entries_count = Column(Integer, nullable=False)
    section_c_offset        = Column(Integer, nullable=False)
    section_c_length        = Column(Integer, nullable=False)
    section_d_offset        = Column(Integer, nullable=False)
    section_d_entries_count = Column(Integer, nullable=False)
    section_d_length        = Column(Integer, nullable=False)
    execution_count         = Column(Integer, nullable=False)
    last_execution_times    = relationship('lastexecutiontime', backref='file_info')

class LastExecutionTime(BaseTable, ConcreteTableMixin):
    '''
    Prefetch file last execution times from file information block
    '''
    file_info_id            = Column(BigInteger, ForeignKey('fileinformation.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)
    last_execution_time     = Column(TIMESTAMP(timezone=True), index=True)

class FileMetric(BaseTable, ConcreteTableMixin, HeaderLinkedMixin):
    '''
    Prefetch file metrics table
    '''
    start_time              = Column(Integer, nullable=False)
    duration                = Column(Integer, nullable=False)
    average_duration        = Column(Integer)
    file_name_offset        = Column(BigInteger, nullable=False)
    file_name_length        = Column(Integer, nullable=False)
    file_name               = relationship('filemetricsname', backref='file_metric')
    file_reference          = relationship('filereference', backref='file_metric')

class FileMetricsName(BaseTable, ConcreteTableMixin, FileMetricsLinkedMixin):
    '''
    Prefetch file metrics entry file name table
    '''
    file_name               = Column(String().with_variant(Text, 'postgresql'))

class TraceChain(BaseTable, ConcreteTableMixin, HeaderLinkedMixin):
    ''''
    Prefetch trace chains table
    '''
    next_entry_index        = Column(Integer, nullable=False)
    sample_duration         = Column(Integer, nullable=False)
    total_block_load_count  = Column(Integer, nullable=False)

class VolumesInformation(BaseTable, ConcreteTableMixin, HeaderLinkedMixin):
    '''
    Prefetch file volume information table
    '''
    volume_device_path_offset   = Column(Integer, nullable=False)
    volume_device_path_length   = Column(Integer, nullable=False)
    volume_create_time          = Column(TIMESTAMP(timezone=True), index=True)
    volume_serial_number        = Column(Integer)
    section_e_offset            = Column(Integer, nullable=False)
    section_e_length            = Column(Integer, nullable=False)
    section_f_offset            = Column(Integer, nullable=False)
    section_f_strings_count     = Column(Integer, nullable=False)
    file_references             = relationship('filereference', backref='volumes_info')
    directory_strings           = relationship('directorystring', backref='volumes_info')

class FileReference(BaseTable, ConcreteTableMixin):
    '''
    Prefetch file references table
    '''
    file_metrics_id         = Column(BigInteger, ForeignKey('filemetrics.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True, index=True)
    volumes_info_id         = Column(BigInteger, ForeignKey('volumesinformation.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True, index=True)
    segment_number          = Column(Integer, nullable=False)
    sequence_number         = Column(Integer, nullable=False)
    __table_args__ = (\
        CheckConstraint('file_metrics_id IS NOT NULL OR volumes_info_id IS NOT NULL'),
    )

class DirectoryStrings(BaseTable, ConcreteTableMixin, VolumesInfoLinkedMixin):
    '''
    Prefetch file directory strings table
    '''
    string                  = Column(String().with_variant(Text, 'postgresql'))
