## -*- coding: UTF-8 -*-
## directives.py
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
import sys
from os import path
from tqdm import tqdm

from adfir.directives import BaseDirective, ParseDirectiveMixin, DBConnectionMixin
from adfir.database.manager import DBManager

class BaseParseFileOutputDirective(ParseDirectiveMixin, BaseDirective):
    '''
    Base class for directives that output results to a file
    '''
    _TASK_CLASS = None

    def __init__(self, args):
        self._frontier = None
        self._pools = None
        super(BaseParseFileOutputDirective, self).__init__(args)
    def _prepare_args(self):
        '''
        @ParseDirectiveMixin._prepare_args
        '''
        assert path.isdir(path.dirname(self.args.target)), 'Target does not point to existing directory'
        self.args.target = path.abspath(self.args.target)
        self.args.target_parent = path.dirname(self.args.target)
    def _prepare_frontier(self):
        '''
        @ParseDirectiveMixin._prepare_frontier
        '''
        self.frontier = self._get_frontier(self.args.sources)
    def _should_parse(self):
        '''
        @ParseDirectiveMixin._should_parse
        '''
        return len(self.frontier) > 0
    def _get_task_kwargs(self):
        '''
        Args:
            N/A
        Returns:
            Dict<String, Any>
            Keyword arguments to pass to add_task method of parser pool
        Preconditions:
            N/A
        '''
        raise NotImplementedError('_get_worker_kwargs not implemented for %s'%type(self).__name__)
    def _get_worker_kwargs(self):
        '''
        Args:
            N/A
        Returns:
            Dict<String, Any>
            Keyword arguments to pass to parser pool when creating worker processes
        Preconditions:
            N/A
        '''
        raise NotImplementedError('_get_worker_kwargs not implemented for %s'%type(self).__name__)
    def _prepare_worker_pools(self):
        '''
        @ParseDirectiveMixin._prepare_worker_pools
        '''
        if self.pools is None:
            self.pools = Container()
        self.pools.progress = parallel.WorkerPool(\
            parallel.JoinableQueue(-1), 
            None,
            daemonize=False,
            worker_class=parallel.ProgressTrackerWorker,
            worker_count=1,
            worker_kwargs=dict(\
                pcount=len(self.frontier),
                pdesc='Total',
                punit='files'\
            )\
        )
        self.pools.parser = parallel.WorkerPool(\
            parallel.JoinableQueue(-1), 
            self._TASK_CLASS, 
            daemonize=False, 
            worker_count=self.args.threads,
            worker_kwargs=self._get_worker_kwargs(),
            task_kwargs=self._get_task_kwargs()\
        )
    def _parse_preamble(self):
        '''
        @ParseDirectiveMixin._parse_preamble
        '''
        tqdm.set_lock(parallel.RLock())
    def _add_tasks(self, node, nodeidx):
        '''
        Args:
            node: String        => filepath of Prefetch file
            nodeidx: Integer    => index of node (Prefetch file) being parsed
        Procedure:
            Add task(s) to parsing queue
        Preconditions:
            node is of type String      (assumed True)
            nodeidx is of type Integer  (assumed True)
        '''
        self.pools.parser.add_task(node, nodeidx)
    def _parse_loop(self):
        '''
        @ParseDirectiveMixin._parse_loop
        '''
        self.pools.progress.start()
        self.pools.parser.start()
        for nodeidx, node in enumerate(self.frontier):
            Logger.info('Parsing prefetch file %s (node %d)'%(node, nodeidx))
            self._add_tasks(node, nodeidx)
        self.pools.parser.join_tasks()
        self.pools.progress.join_tasks()
        self.pools.progress.add_poison_pills()
        self.pools.progress.join_workers()
        self.pools.parser.add_poison_pills()
        self.pools.parser.join_workers()
    def _parse_postamble(self):
        '''
        @ParseDirectiveMixin._parse_postamble
        '''
        parallel.coalesce_files(path.join(self.args.target_parent, '*_tmp_apf.out'), self.args.target)

class ParseJSONDirective(BaseParseFileOutputDirective):
    '''
    Directive for parsing Prefetch file to JSON format
    '''
    _TASK_CLASS = tasks.ParseJSONTask

    def _get_task_kwargs(self):
        '''
        @BaseParseFileOutputDirective._get_task_kwargs
        '''
        return dict(target=self.args.target_parent, pretty=self.args.pretty if self.args.threads == 1 else False)
    def _get_worker_kwargs(self):
        '''
        @BaseParseFileOutputDirective._get_worker_kwargs
        '''
        return dict(result_queue=self.pools.progress.queue, log_path=self.args.log_path)
    def run(self):
        '''
        Args:
            @BaseDirective.run_directive
            args.sources: List<String>  => list of Prefetch file(s) to parse
            args.target: String         => path to output file
            args.pretty                 => whether to pretty print JSON output
        Procedure:
            Parse Prefetch information to JSON format
        Preconditions:
            @BaseDirective.run_directive
            args.sources is of type List<String>    (assumed True)
            args.target is of type String           (assumed True)
            args.target points to existing directory
            args.pretty is of type Boolean          (assumed True)
        '''
        super(ParseJSONDirective, self).run()

class ParseJSONDirective(ParseDirectiveMixin, BaseDirective):
    '''
    Directive for parsing Prefetch file to JSON format
    '''
    pass

class ParseDBDirective(ParseDirectiveMixin, DBConnectionMixin, BaseDirective):
    '''
    Directive for parsing Prefetch file to DB format
    '''
    def __init__(self, args):
        BaseDirective.__init__(self, args)
    @property
    def manager(self):
        '''
        Getter for manager (database connection manager)
        '''
        return self.__manager
    @manager.setter
    def manager(self, value):
        '''
        Setter for manager
        '''
        assert isinstance(value, DBManager)
        self.__manager = value
    def _preamble(self):
        '''
        @BaseDirective._preamble
        '''
        self.manager = DBManager(conn_string=self.conn_string, metadata=self.args.metadata)
        self.manager.initialize(bootstrap=True)
        self.manager.engine.dispose()
        self.manager = None
    def _should_parse(self):
        '''
        @ParseDirectiveMixin._should_parse
        '''
        return len(self.frontier) > 0
    def _prepare_worker_pools(self):
        '''
        @ParseDirectiveMixin._prepare_worker_pools
        '''
        if self.pools is None:
            self.pools = Container()
        self.pools.progress = parallel.WorkerPool(\
            parallel.JoinableQueue(-1), 
            tasks.ParseDBTaskStage2,
            daemonize=False, 
            worker_class=parallel.DBProgressTrackerWorker,
            worker_count=1,
            worker_kwargs=dict(\
                log_path=self.args.log_path,
                pcount=len(self.frontier),
                pdesc='Total',
                punit='files',
                manager=DBManager(conn_string=self.conn_string)\
            )\
        )
        self.pools.parser = parallel.WorkerPool(\
            parallel.JoinableQueue(-1), 
            tasks.ParseDBTaskStage1, 
            daemonize=False, 
            worker_count=self.args.threads,
            worker_kwargs=dict(\
                result_queue=self.pools.progress.queue, 
                log_path=self.args.log_path\
            )
        )
    def _parse_preamble(self):
        '''
        @ParseDirectiveMixin._parse_preamble
        '''
        tqdm.set_lock(parallel.RLock())
    def _parse_loop(self):
        '''
        @ParseDirectiveMixin._parse_loop
        '''
        self.pools.progress.start()
        self.pools.parser.start()
        for nodeidx, node in enumerate(self.frontier):
            Logger.info('Parsing prefetch file %s (node %d)'%(node, nodeidx))
            self.pools.parser.add_task(node)
        self.pools.parser.join_tasks()
        self.pools.progress.join_tasks()
        self.pools.progress.add_poison_pills()
        self.pools.progress.join_workers()
        self.pools.parser.add_poison_pills()
        self.pools.parser.join_workers()
    def _postamble(self):
        '''
        @ParseDirectiveMixin._parse_postamble
        '''
        
    def run(self):
        '''
        Args:
            N/A
        Procedure:
            Parse Prefetch information to database
            self.args.db_driver is of type String
            self.args.db_name is of type String
            self.args.db_conn_string is of type String
            self.args.db_user is of type String
            self.args.db_passwd is of type String
            self.args.db_host is of type String
            self.args.db_port is of type String
            one of the following conditions must be true:
                1) self.args.db_driver is sqlite and self.args.db_name is a valid path
                2) self.args.db_conn_string is not None and is valid connection string 
                3) self.args.db_user, self.args.db_passwd, self.args.db_host, and self.args.db_port are not None
        '''
        super(ParseDBDirective, self).run()

class DBQueryDirective(BaseDirective, DBConnectionMixin):
    '''
    Directive for querying a DB
    '''
    def run(self):
        '''
        Args:
            @BaseDirective.run_directive
            @ParseDBDirective.run (args.db_*)
            @ParseCSVDirective.run (args.target, args.sep)
            args.query: String  => database query to submit
            args.title: String  => title of table
        Procedure:
            Query $MFT information from database
        Preconditions:
            @BaseDirective.run_directive
            @ParseDBDirective.run (args.db_*)
            @ParseCSVDirective.run (args.target, args.sep)
            args.query is of type String
            args.title is of type String
        '''
        assert isinstance(self.args.query, str), 'Query is not of type String'
        if self.args.target is not None:
            assert path.isdir(path.dirname(self.args.target)), 'Target does not point to existing directory'
        conn_string = self._prepare_conn_string(self.args)
        manager = DBManager(conn_string=conn_string, metadata=db.BaseTable.metadata)
        manager.initialize(create_session=True)
        try:
            result_proxy = manager.session.execute(text(self.args.query))
        except Exception as e:
            Logger.error('Failed to submit query to database (%s)'%(str(e)))
        else:
            headers = result_proxy.keys()
            resultset = result_proxy.fetchall()
            if len(resultset) > 0:
                if self.args.target is not None:
                    self.args.target = path.abspath(self.args.target)
                    try:
                        with open(self.args.target, 'a') as target:
                            target.write(self.args.sep.join(headers) + '\n')
                            for result in resultset:
                                try:
                                    target.write(self.args.sep.join([str(item) for item in result]) + '\n')
                                except Exception as e:
                                    Logger.error('Failed to write result to output file %s (%s)'%(self.args.target, str(e)))
                    except Exception as e:
                        Logger.error('Failed to write results to output file %s (%s)'%(self.args.target, str(e)))
                else:
                    if sys.stdout.isatty():
                        table_data = [headers]
                        for result in resultset:
                            table_data.append([str(item) for item in result])
                        table = AsciiTable(table_data)
                        if self.args.title:
                            table.title = self.args.title
                        print(table.table)
                    else:
                        print(self.args.sep.join(headers))
                        for result in resultset:
                            print(self.args.sep.join([str(item) for item in result]))
            else:
                Logger.info('No results found for query %s'%self.args.query)
