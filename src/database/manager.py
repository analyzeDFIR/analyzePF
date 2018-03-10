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

import os.path
from sqlalchemy import create_engine, MetaData
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from flask import Flask, current_app

class RunManager(object):
    '''
    Class for managing state of database connection
    '''
    def __init__(self, engine=None, metadata=None, session_factory=None, session=None, scoped=False):
        self._engine = engine
        self._metadata = metadata
        self._session_factory = session_factory
        self._session = session
        self._scoped_sessions = scoped
    def _get_engine(self):
        '''
        '''
        return self._engine
    def _get_metadata(self):
        '''
        '''
        return self._metadata
    def _get_session_factory(self):
        '''
        '''
        return self._session_factory
    def get_session(self, persist=True):
        '''
        '''
        if self._scoped_sessions:
            return self._session_factory
        if persist:
            if self._session is None:
                self._set_session(self._create_session())
            return self._session
        return self._create_session()
    def _set_engine(self, engine):
        '''
        '''
        assert isinstance(engine, Engine)
        self._engine = engine
    def _set_metadata(self, metadata):
        '''
        '''
        assert isinstance(metadata, MetaData)
        self._metadata = metadata
    def _set_session_factory(self, session_factory):
        '''
        '''
        assert callable(session_factory)
        self._session_factory = session_factory
    def _set_session(self, session):
        '''
        '''
        assert isinstance(session, Session)
        self._session = session
    def _create_session(self):
        '''
        '''
        if self._session_factory is not None:
            return (self._get_session_factory())()
        return None
    def close_session(self, session=None):
        '''
        '''
        assert session is None or isinstance(session, Session)
        if session is not None:
            session.close()
        elif self._scoped_sessions and self._session_factory is not None:
            self._session_factory.remove()
        elif self._session is not None:
            self.get_session().close()
        return True
    def _flask_teardown_appcontext(self, err):
        '''
        '''
        if current_app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN']:
            if err is None:
                self.get_session().commit()
        self.get_session().remove()
        return err
    def bootstrap(self, engine=None):
        '''
        '''
        assert engine is None or isinstance(engine, Engine)
        if engine is not None:
            self._set_engine(engine)
        if self._get_engine() is not None and self._get_metadata() is not None:
            self._get_metadata().create_all(self._get_engine())
            return True
        return False
    def initialize(self, app, conn_string=None, metadata=None, bootstrap=False, scoped=False, create_session=False):
        '''
        '''
        assert isinstance(app, Flask), 'App is not of type Flask'
        assert isinstance(conn_string, (type(None), str)), 'Conn_string is not of type str'
        assert (metadata is None and self._get_metadata() is not None) or isinstance(metadata, MetaData), 'Metadata is not of type MetaData'
        assert isinstance(bootstrap, bool), 'Bootstrap is not of type boolean'
        assert isinstance(scoped, bool), 'Scoped is not of type boolean'
        assert isinstance(create_session, bool), 'Create_session is not of type boolean'
        app.config.setdefault('SQLALCHEMY_DATABASE_URI', 'sqlite:///pman.db')
        app.config.setdefault('SQLALCHEMY_COMMIT_ON_TEARDOWN', False)
        app.teardown_appcontext_funcs.append(self._flask_teardown_appcontext)
        conn_string = conn_string if conn_string is not None else app.config['SQLALCHEMY_DATABASE_URI']
        try:
            if conn_string is not None:
                self._set_engine(create_engine(conn_string))
            if metadata is not None:
                self._set_metadata(metadata)
            if bootstrap:
                self.bootstrap()
            if scoped or self._scoped_sessions:
                self._set_session_factory(scoped_session(sessionmaker(bind=self._get_engine(), autoflush=False)))
                self._scoped_sessions = True
            else:
                self._set_session_factory(sessionmaker(bind=self._get_engine(), autoflush=False))
                self._scoped_sessions = False
            if create_session and not self._scoped_sessions:
                self._set_session(self._create_session())
            app.rm = self
            return True, None
        except Exception as e:
            raise
            return False, str(e)
    def query(self, model, **kwargs):
        '''
        Args:
            model: BaseTable    => model of table to query
            **kwargs: Any       => field to filter on
        Returns:
            SQLAlchemy query object if no error thrown, None otherwise
        Preconditions:
            model is base class of BaseTable (assumed True)
        '''
        try:
            query = self.get_session().query(model)
            for arg in kwargs:
                query = query.filter(getattr(model, arg) == kwargs[arg])
            return query
        except:
            return None
    def add(self, record, commit=False):
        '''
        Args:
            record: BaseTable   => record to add to current session
        Procedure:
            Add record to current session and commit if True
        Preconditions:
            record is instance of BaseTable
        '''
        self.get_session().add(record)
        if commit:
            self.get_session().commit()
        return self
    def delete(self, record, commit=False):
        '''
        Args:
            record: BaseTable   => record to add to current session
        Procedure:
            Add record to current session and commit if True
        Preconditions:
            record is instance of BaseTable
        '''
        self.get_session().delete(record)
        if commit:
            self.get_session().commit()
        return self
    def commit(self):
        '''
        Args:
            N/A
        Procedure:
            Commit current session
        Preconditions:
            N/A
        '''
        self.get_session().commit()
        return self
