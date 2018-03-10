## -*- coding: UTF-8 -*-
## database.py
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

from sqlalchemy.schema import Table, Column, MetaData, DDLElement
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import ClauseElement, FromClause
from sqlalchemy.event import listen

class TimestampDefaultExpression(ClauseElement):
    ''''
    Class to generate server default timestamp expressions based
    on SQL dialect.
    '''
    pass

@compiles(TimestampDefaultExpression, 'mssql')
def generate_timestamp_expression(element, compiler, **kwargs):
    return 'GETUTCDATE()'
@compiles(TimestampDefaultExpression, 'mysql')
def generate_timestamp_expression(element, compiler, **kwargs):
    return 'UTC_TIMESTAMP()'
@compiles(TimestampDefaultExpression, 'oracle')
def generate_timestamp_expression(element, compiler, **kwargs):
    return 'SYS_EXTRACT_UTC(SYSTIMESTAMP)'
@compiles(TimestampDefaultExpression, 'postgresql')
def generate_timestamp_expression(element, compiler, **kwargs):
    return '(NOW() AT TIME ZONE \'UTC\')'
@compiles(TimestampDefaultExpression, 'sqlite')
def generate_timestamp_expression(element, compiler, **kwargs):
    return 'CURRENT_TIMESTAMP'

class CreateViewExpression(DDLElement):
    '''
    Class to allow easy creation of views 
    (implementation taken from 
    http://www.jeffwidman.com/blog/847/using-sqlalchemy-to-create-and-manage-postgresql-materialized-views/)
    '''
    def __init__(self, name, selectable):
        self.name = name
        self.selectable = selectable

@compiles(CreateViewExpression)
def generate_mview_create_expression(element, compiler, **kwargs):
    return 'CREATE OR REPLACE VIEW %s AS %s'%(\
        element.name,\
        compiler.sql_compiler.process(element.selectable, literal_binds=True))

class CreateMaterializedViewExpression(CreateViewExpression):
    '''
    Class to allow easy creation of materialized views 
    in PostgreSQL (implementation taken from 
    http://www.jeffwidman.com/blog/847/using-sqlalchemy-to-create-and-manage-postgresql-materialized-views/)
    '''
    pass

@compiles(CreateMaterializedViewExpression)
def generate_mview_create_expression(element, compiler, **kwargs):
    return 'CREATE OR REPLACE VIEW %s AS %s'%(\
        element.name,\
        sql_compiler.process(element.selectable, literal_binds=True))
@compiles(CreateMaterializedViewExpression, 'postgresql')
def generate_mview_create_expression(element, compiler, **kwargs):
    return 'CREATE OR REPLACE MATERIALIZED VIEW %s AS %s'%(\
        element.name,\
        sql_compiler.process(element.selectable, literal_binds=True))

class DropViewExpression(DDLElement):
    '''
    Class to allow easy deletion of views
    '''
    def __init__(self, name):
        self.name = name

@compiles(DropViewExpression)
def generate_mview_drop_expression(element, compiler, **kwargs):
    return 'DROP VIEW IF EXISTS %s'%(element.name)

class DropMaterializedViewExpression(DropViewExpression):
    '''
    Class to allow easy deletion of materialized views in PostgreSQL
    '''
    pass

@compiles(DropMaterializedViewExpression)
def generate_mview_drop_expression(element, compiler, **kwargs):
    return 'DROP VIEW IF EXISTS %s'%(element.name)
@compiles(DropMaterializedViewExpression, 'postgresql')
def generate_mview_drop_expression(element, compiler, **kwargs):
    return 'DROP MATERIALIZED VIEW IF EXISTS %s'%(element.name)

def create_view(name, selectable, metadata, materialized=False):
    '''
    Args:
        name: String            => name of materialized view to create
        selectable: FromClause  => query to create view as
        metadata: MetaData      => metadata to listen for events on
        materialized: Boolean   => whether to create standard or materialized view
    Returns:
        Table object bound to temporary MetaData object with columns as
        columns returned from selectable (essentially creates table as view)
        NOTE:
            For non-postgresql backends, creating a materialized view
            will result in a standard view, which cannot be indexed
    Preconditions:
        name is of type String
        selectable is of type FromClause
        metadata is of type Metadata
        materialized is of type Boolean
    '''
    assert isinstance(name, str), 'Name is not of type String'
    assert isinstance(selectable, FromClause), 'Selectable is not of type FromClause'
    assert isinstance(metadata, MetaData), 'Metadata is not of type MetaData'
    assert isinstance(materialized, bool), 'Materialized is not of type Boolean'
    _tmp_mt = MetaData()
    tbl = Table(name, _tmp_mt)
    for c in selectable.c:
        tbl.append_column(Column(c.name, c.type, primary_key=c.primary_key))
    listen(\
        metadata,\
        'after_create',\
        CreateMaterializedViewExpression(name, selectable) if materialized else CreateViewExpression(name, selectable))
    listen(\
        metadata,\
        'before_drop',\
        DropMaterializedViewExpression(name) if materialized else DropViewExpression(name))
    return tbl
