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
from sqlalchemy.orm import relationship
from sqlalchemy.types import String, Text, Integer, BigInteger, Boolean
from sqlalchemy import Column, ForeignKey, Index, text
from sqlalchemy.schema import UniqueConstraint, CheckConstraint, DDL
from sqlalchemy.ext.declarative import declarative_base, declared_attr

from src.utils.database import TimestampDefaultExpression, create_view 

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

class MetadataLinkedMixin(object):
    '''
    Mixin for tables linked to metadata table
    metadata table serves as accounting system for parser
    '''
    meta_id               = Column(BigInteger, ForeignKey('metadata.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)

class HeaderLinkedMixin(object):
    '''
    Mixin for tables linked to header table
    '''
    header_id               = Column(BigInteger, ForeignKey('header.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)

class FileMetricsLinkedMixin(obejct):
    '''
    Mixin for tables linked to filemetrics table
    '''
    file_metrics_id         = Column(BigInteger, ForeignKey('filemetrics.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)

class VolumesInfoLinkedMixin(obejct):
    '''
    Mixin for tables linked to volumesinformation table
    '''
    volumes_info_id         = Column(BigInteger, ForeignKey('volumesinformation.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)

class Metadata(BaseTable, ConcreteTableMixin):
    '''
    Parsed prefetch file metadata table
    '''
    file_name               = Column(String().with_variant(Text, 'postgresql'), nullable=False)
    file_path               = Column(String().with_variant(Text, 'postgresql'), nullable=False)
    file_size               = Column(BigInteger, nullable=False)
    md5hash                 = Column(String().with_variant(Text, 'postgresql'), nullable=False)
    sha1hash                = Column(String().with_variant(Text, 'postgresql'), nullable=False)
    sha2hash                = Column(String().with_variant(Text, 'postgresql'), nullable=False)
    modify_time             = Column(TIMESTAMP(timezone=True))
    access_time             = Column(TIMESTAMP(timezone=True))
    create_time             = Column(TIMESTAMP(timezone=True))
    completed               = Column(Boolean, index=True)

class Header(BaseTable, ConcreteTableMixin, MetadataLinkedMixin):
    '''
    Prefetch file header table
    '''
    version                 = Column(String().with_variant(Text, 'postgresql'), nullable=False, index=True)
    file_size               = Column(BigInteger, nullable=False)
    executable_name         = Column(String().with_variant(Text, 'postgresql'), nullable=False, index=True)
    prefetch_hash           = Column(String().with_variant(Text, 'postgresql'), nullable=False, index=True)

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

class LastExecutionTime(BaseTable, ConcreteTableMixin):
    '''
    Prefetch file last execution times from file information block
    '''
    file_info_id            = Column(BigInteger, ForeignKey('fileinformation.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)
    last_execution_time     = Column(TIMESTAMP(timezone=True), index=True)

class FileMetrics(BaseTable, ConcreteTableMixin, HeaderLinkedMixin):
    '''
    Prefetch file metrics table
    '''
    start_time              = Column(Integer, nullable=False)
    duration                = Column(Integer, nullable=False)
    average_duration        = Column(Integer)
    file_name_offset        = Column(BigInteger, nullable=False)
    file_name_length        = Column(Integer, nullable=False)

class FileMetricsNames(BaseTable, ConcreteTableMixin, FileMetricsLinkedMixin):
    '''
    Prefetch file metrics entry file name table
    '''
    file_name               = Column(String().with_variant(Text, 'postgresql'))

class TraceChains(BaseTable, ConcreteTableMixin, HeaderLinkedMixin):
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

class FileReferences(BaseTable, ConcreteTableMixin):
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
