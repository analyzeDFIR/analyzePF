## -*- coding: UTF8 -*-
## manager.py
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

import logging
Logger = logging.getLogger(__name__)
import os.path
from sqlalchemy import create_engine, MetaData
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session

class DBManager(object):
    '''
    Class for managing state of database connection
    '''
    def __init__(self, conn_string=None, metadata=None, session_factory=None, session=None, scoped=False):
        self._conn_string = conn_string
        self._metadata = metadata
        self._session_factory = session_factory
        self._session = session
        self._scoped_sessions = scoped
        self._engine = None
    @property
    def conn_string(self):
        '''
        @conn_string.getter
        '''
        return self._conn_string
    @conn_string.setter
    def conn_string(self, value):
        '''
        @conn_string.setter
        Preconditions:
            conn_string is of type String
        '''
        assert isinstance(conn_string, str), 'Conn_string is not of type String'
        self._conn_string = value
    @property
    def engine(self):
        '''
        @engine.getter
        '''
        return self._engine
    @engine.setter
    def engine(self, value):
        '''
        @engine.setter
        Preconditions:
            value is of type Engine
        '''
        assert isinstance(value, Engine)
        self._engine = value
    def create_engine(self, conn_string=None, persist=True):
        '''
        Args:
            conn_string: String     => database connection string
            persist: True           => whether to persist the database engine
        Returns:
            Engine
            New database engine using either provided conn_string
            or self.conn_string
        Preconditions:
            conn_string is of type String
            persist is of type Boolean
        '''
        assert isinstance(conn_string, (type(None), str)), 'Conn_string is not of type String'
        assert isinstance(persist, bool), 'Persist is not of type Boolean'
        if conn_string is not None:
            self.conn_string = conn_string
        if self.conn_string is not None:
            engine = create_engine(self.conn_string)
            if persist:
                self.engine = engine
            return engine
    @property
    def metadata(self):
        '''
        @metadata.getter
        '''
        return self._metadata
    @metadata.setter
    def metadata(self, value):
        '''
        @metadata.setter
        Preconditions:
            value is of type MetaData
        '''
        assert value is None or isinstance(value, MetaData)
        self._metadata = value
    @property
    def session_factory(self):
        '''
        @session_factory.getter
        '''
        return self._session_factory
    @session_factory.setter
    def session_factory(self, value):
        '''
        @session_factory.setter
        Preconditions:
            value is of type Callable
        '''
        assert value is None or callable(value)
        self._session_factory = value
    @property
    def session(self):
        '''
        @_session.getter
        '''
        return self._session
    @session.setter
    def session(self, value):
        '''
        @_session.setter
        '''
        assert isinstance(value, (type(None), Session))
        self._session = value
    def create_session(self, persist=True):
        '''
        Args:
            persist: Boolean    => whether to persist the session
        Returns:
            Session
            Either new session object or pre-existing session
            NOTE:
                If _session_factory is None, this will throw an error
        Preconditions:
            persist is of type Boolean
        '''
        assert isinstance(persist, bool), 'Persist is not of type Boolean'
        if self._scoped_sessions:
            return self.session_factory
        if persist:
            if self.session is None:
                self.session = self.session_factory()
            return self.session
        return self.session_factory()
    def close_session(self, session=None):
        '''
        Args:
            session: Session    => session to close if not self.session
        Procedure:
            Closes either the provided session or the current session
            at self.session
        Preconditions:
            session is of type Session
        '''
        assert session is None or isinstance(session, Session)
        if session is not None:
            session.close()
        elif self._scoped_sessions and self.session_factory is not None:
            self.session_factory.remove()
        elif self.session is not None:
            self.session.close()
            self.session = None
    def bootstrap(self, engine=None):
        '''
        Args:
            engine: Engine  => the connection engine to use
        Procedure:
            Use a connection engine to bootstrap a database
            with the necessary tables, indexes, and (materialized) view
        Preconditions:
            engine is of type Engine
        '''
        assert engine is None or isinstance(engine, Engine)
        if engine is not None:
            self.engine = engine
        if self.engine is not None and self.metadata is not None:
            self.metadata.create_all(self.engine)
    def initialize(self, conn_string=None, metadata=None, bootstrap=False, scoped=False, create_session=False):
        '''
        Args:
            conn_string: String     => database connection string
            metadata: MetaData      => database metadata object
            bootstrap: Boolean      => whether to bootstrap database with table, index, and view information
            scoped: Boolean         => whether to use scoped session objects (see: http://docs.sqlalchemy.org/en/latest/orm/contextual.html)
            create_session: Boolean => whether to create a persisted session on initialization
        Procedure:
            initialize a database connection using conn_string and perform various setup tasks if asked to
        Preconditions:
            conn_string is of type String
            metadata is of type MetaData
            bootstrap is of type Boolean
            scoped is of type Boolean
            create_session is of type Boolean
        '''
        assert isinstance(conn_string, (type(None), str)), 'Conn_string is not of type String'
        assert (metadata is None and self.metadata is not None) or isinstance(metadata, MetaData), 'Metadata is not of type MetaData'
        assert isinstance(bootstrap, bool), 'Bootstrap is not of type boolean'
        assert isinstance(scoped, bool), 'Scoped is not of type boolean'
        assert isinstance(create_session, bool), 'Create_session is not of type boolean'
        try:
            if conn_string is not None:
                self.conn_string = conn_string
            self.create_engine()
            if metadata is not None:
                self.metadata = metadata
            if self.engine is not None:
                if bootstrap:
                    self.bootstrap()
                if scoped or self._scoped_sessions:
                    self.session_factory = scoped_session(sessionmaker(bind=self.engine, autoflush=False))
                    self._scoped_sessions = True
                else:
                    self.session_factory = sessionmaker(bind=self.engine, autoflush=False)
                    self._scoped_sessions = False
                if create_session and not self._scoped_sessions:
                    self.create_session()
        except Exception as e:
            Logger.error('Failed to initialize DBManager (%s)'%str(e))
    def query(self, model, **kwargs):
        '''
        Args:
            model: BaseTable    => model of table to query
            **kwargs: Any       => field to filter on
        Returns:
            Query
            Query object if no error thrown, None otherwise
        Preconditions:
            model is base class of BaseTable (assumed True)
        '''
        try:
            query = self.session.query(model)
            for arg in kwargs:
                query = query.filter(getattr(model, arg) == kwargs[arg])
            return query
        except:
            return None
    def add(self, record, session=None, commit=False):
        '''
        Args:
            record: BaseTable   => record to add to current session
            session: Session    => session to add record to
            commit: Boolean     => whether to commit and end the transaction block
        Procedure:
            DBManager
            Add record to either provided or current session and potentially commit
        Preconditions:
            record is instance of BaseTable
            session is of type Session
            commit is of type Boolean
        '''
        if session is None:
            session = self.session
        session.add(record)
        if commit:
            self.commit(session)
        return self
    def delete(self, record, session=None, commit=False):
        '''
        Args:
            record: BaseTable   => record to add to current session
            session: Session    => session to add record to
            commit: Boolean     => whether to commit and end the transaction block
        Procedure:
            DBManager
            Delete record using either provided session or current session 
            and potentially commit
        Preconditions:
            record is instance of BaseTable
            session is of type Session
            commit is of type Boolean
        '''
        if session is None:
            session = self.session
        session.delete(record)
        if commit:
            self.commit(session)
        return self
    def commit(self, session=None):
        '''
        Args:
            session: Session    => session to add record to
        Procedure:
            Commit either provided or current session
        Preconditions:
            session is of type Session
        '''
        if session is None:
            session = self.session
        session.commit()
        return self
    def rollback(self, session=None):
        '''
        Args:
            session: Session    => session to add record to
        Procedure:
            Rollback either provided or current session
        Preconditions:
            session is of type Session
        '''
        if session is None:
            session = self.session
        session.rollback()
        return self
