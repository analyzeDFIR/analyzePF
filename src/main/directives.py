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
from os import path, stat
from glob import glob
from argparse import Namespace
from time import sleep
from tqdm import tqdm

from src.utils.config import initialize_logger, synthesize_log_path
from src.utils.registry import RegistryMetaclassMixin 
import src.utils.parallel as parallel
import src.main.tasks as tasks

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
        if cls.retrieve(name) is not None or name.startswith('Base'):
            return False
        if not hasattr(new_cls, 'run_directive') or not callable(new_cls.run_directive):
            return False
        cls._REGISTRY.update({name: new_cls})
        return True

class BaseDirective(object, metaclass=DirectiveRegistry):
    '''
    Base class for creating new directives. This
    class is not included in the registry of directives
    exposed to the command line interface and should not
    be referenced outside of this module unless type checking
    a directive class.
    '''
    _TASK_CLASS = None

    @staticmethod
    def get_frontier(sources):
        '''
        Args:
            sources: List<String>   => list of source paths
        Returns:
            List<String>
            List of existing source files to parse (supplied files and
            files from supplied directories)
        Preconditions:
            sources is of type List<String> (asssumed True)
        '''
        frontier = list()
        for src in sources:
            src = path.abspath(src)
            if path.isfile(src):
                frontier.append(src)
            elif path.isdir(src):
                for subsrc in glob(path.join(src, '*')):
                    frontier.append(subsrc)
        return frontier
    @classmethod
    def run(cls, args):
        '''
        Args:
            @BaseDirective.run_directive
        Procedure:
            Entry point for directive
        Preconditions:
            @BaseDirective.run_directive
        '''
        raise NotImplementedError('method run not implemented for %s'%cls.__name__)
    @classmethod
    def run_directive(cls, args):
        '''
        Args:
            args: Namespace => parsed command line arguments
                args.log_path: String   => path to log file directory
                args.log_prefix: String => log file prefix
                args.threads: Integer   => number of threads to use
        Procedure:
            Initialize the logging system and run this directive using the supplied arguments
        Preconditions:
            args is of type Namespace
            args.log_path is of type String
            args.log_prefix is of type String
            args.threads is of type Integer > 0
            ** Any other preconditions must be checked by subclasses
        '''
        assert isinstance(args, Namespace), 'Args is not of type Namespace'
        assert hasattr(args, 'log_path'), 'Args does not contain log_path attribute'
        assert hasattr(args, 'log_prefix'), 'Args does not contain log_prefix attribute'
        assert hasattr(args, 'threads'), 'Args does not contain threads attribute'
        assert args.threads > 0, 'Threads is not greater than 0'
        if args.threads > parallel.CPU_COUNT:
            args.threads = parallel.CPU_COUNT
        initialize_logger(args.log_path)
        Logger.info('BEGIN: %s'%cls.__name__)
        cls.run(args)
        sleep(1)
        Logger.info('END: %s'%cls.__name__)
        logging.shutdown()
        log_path = synthesize_log_path(args.log_path, args.log_prefix)
        parallel.coalesce_files(path.join(args.log_path, '*_tmp_apf.log'), log_path)

    def __init__(self, args):
        self.run_directive(args)

class BaseParseFileOutputDirective(BaseDirective):
    '''
    Base class for directives that output results to a file
    '''
    _TASK_CLASS = None

    @classmethod
    def _get_task_kwargs(cls, args):
        '''
        Args:
            args: Namespace => command line arguments
        Returns:
            Dict<String, Any>
            Keyword arguments to be supplied to tasks for worker pool
        Preconditions:
            args is of type Namespace   (assumed True)
        '''
        raise NotImplementedError('_get_worker_kwargs not implemented for %s'%cls.__name__)
    @classmethod
    def _get_worker_kwargs(cls, args):
        '''
        Args:
            args: Namespace => command line arguments
        Returns:
            Dict<String, Any>
            Keyword arguments to be supplied to workers in pool
        Preconditions:
            args is of type Namespace   (assumed True)
        '''
        raise NotImplementedError('_get_worker_kwargs not implemented for %s'%cls.__name__)
    @classmethod
    def run(cls, args):
        '''
        @BaseDirective.run
        '''
        assert path.isdir(path.dirname(args.target)), 'Target does not point to existing directory'
        args.target = path.abspath(args.target)
        args.target_parent = path.dirname(args.target)
        frontier = cls.get_frontier(args.sources)
        frontier_count = len(frontier)
        if frontier_count > 0 and cls._TASK_CLASS is not None:
            tqdm.set_lock(parallel.RLock())
            progress_pool = parallel.WorkerPool(\
                parallel.JoinableQueue(-1), 
                None,
                worker_class=parallel.ProgressTrackerWorker,
                worker_count=1,
                worker_kwargs=dict(\
                    pcount=frontier_count,
                    pdesc='Total',
                    punit='files'\
                )\
            )
            args.result_queue = progress_pool.queue
            worker_pool = parallel.WorkerPool(\
                parallel.JoinableQueue(-1), 
                cls._TASK_CLASS, 
                daemonize=False, 
                worker_count=args.threads,
                worker_kwargs=cls._get_worker_kwargs(args),
                task_kwargs=cls._get_task_kwargs(args)\
            )
            progress_pool.start()
            worker_pool.start()
            for nodeidx, node in enumerate(frontier):
                Logger.info('Parsing prefetch file %s (node %d)'%(node, nodeidx))
                prefetch_file = open(node, 'rb')
                try:
                    worker_pool.add_task(nodeidx, node)
                finally:
                    prefetch_file.close()
            worker_pool.join_tasks()
            progress_pool.join_tasks()
            progress_pool.add_poison_pills()
            progress_pool.join_workers()
            worker_pool.add_poison_pills()
            worker_pool.join_workers()
            parallel.coalesce_files(path.join(args.target_parent, '*_tmp_apf.out'), args.target)

class ParseCSVDirective(BaseParseFileOutputDirective):
    '''
    Directive for parsing Prefetch file to CSV format
    '''
    _TASK_CLASS = tasks.ParseCSVTask

    @classmethod
    def _get_task_kwargs(cls, args):
        '''
        @BaseParseFileOutputDirective._get_task_kwargs
        '''
        return dict(info_type=args.info_type, target=args.target_parent, sep=args.sep)
    @classmethod
    def _get_worker_kwargs(cls, args):
        '''
        @BaseParseFileOutputDirective._get_worker_kwargs
        '''
        return dict(result_queue=args.result_queue, log_path=args.log_path)
    @classmethod
    def run(cls, args):
        '''
        Args:
            @BaseDirective.run_directive
            args.info_type: String      => type of information to extract
            args.sources: List<String>  => list of Prefetch file(s) to parse
            args.target: String         => path to output file
            args.sep: String            => separator to use in output file
        Procedure:
            Parse Prefetch information to CSV format
            FIELDS: Version Signature ExecutableName PrefetchHash
                    SectionAEntriesCount SectionBEntriesCount SectionCLength SectionDEntriesCount
                    LastExecutionTime ExecutionCount VolumeDevicePath VolumeCreateTime VolumeSerialNumber
                    FileMetricsCount TraceChainsAccount FileReferenceCount DirectoryStringsCount FileNameStrings
        Preconditions:
            @BaseDirective.run_directive
            args.info_type is of type String        (assumed True)
            args.sources is of type List<String>    (assumed True)
            args.target is of type String           (assumed True)
            args.target points to existing directory
            args.sep is of type String              (assumed True)
        '''
        super(ParseCSVDirective, cls).run(args)

class ParseBODYDirective(BaseParseFileOutputDirective):
    '''
    Directive for parsing Prefetch file to BODY format
    '''
    _TASK_CLASS = tasks.ParseBODYTask

    @classmethod
    def _get_task_kwargs(cls, args):
        '''
        @BaseParseFileOutputDirective._get_task_kwargs
        '''
        return dict(target=args.target_parent, sep=args.sep)
    @classmethod
    def _get_worker_kwargs(cls, args):
        '''
        @BaseParseFileOutputDirective._get_worker_kwargs
        '''
        return dict(result_queue=args.result_queue, log_path=args.log_path)
    @classmethod
    def run(cls, args):
        '''
        Args:
            @BaseDirective.run_directive
            args.sources: List<String>  => list of Prefetch file(s) to parse
            args.target: String         => path to output file
            args.sep: String            => separator to use in output file
        Procedure:
            Parse Prefetch information to BODY format
            FIELDS: nodeidx|recordidx|MD5|name|inode|mode_as_string|UID|GID|size|atime|mtime|ctime|crtime
        Preconditions:
            @BaseDirective.run_directive
            args.sources is of type List<String>    (assumed True)
            args.target is of type String           (assumed True)
            args.target points to existing directory
            args.sep is of type String              (assumed True)
        '''
        super(ParseBODYDirective, cls).run(args)

class ParseJSONDirective(BaseParseFileOutputDirective):
    '''
    Directive for parsing Prefetch file to JSON format
    '''
    _TASK_CLASS = tasks.ParseJSONTask

    @classmethod
    def _get_task_kwargs(cls, args):
        '''
        @BaseParseFileOutputDirective._get_task_kwargs
        '''
        return dict(target=args.target_parent, pretty=args.pretty if args.threads == 1 else False)
    @classmethod
    def _get_worker_kwargs(cls, args):
        '''
        @BaseParseFileOutputDirective._get_worker_kwargs
        '''
        return dict(result_queue=args.result_queue, log_path=args.log_path)
    @classmethod
    def run(cls, args):
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
        super(ParseJSONDirective, cls).run(args)

class ParseDBDirective(BaseDirective):
    '''
    Directive for parsing Prefetch file to DB format
    '''
    @classmethod
    def run(cls, args):
        '''
        Args:
            @BaseDirective.run_directive
            args.db_driver: String      => database db_driver to use
            args.db_name: String        => name of database to connect to
            args.db_conn_string: String => database connection string
            args.db_user: String        => name of database user
            args.db_passwd: String      => password of database user
            args.db_host: String        => hostname (IP address) of database
            args.db_port: String        => port database is listening on
        Procedure:
            Parse Prefetch information to database
        Preconditions:
            @BaseDirective.run_directive
            args.db_driver is of type String
            args.db_name is of type String
            args.db_conn_string is of type String
            args.db_user is of type String
            args.db_passwd is of type String
            args.db_host is of type String
            args.db_port is of type String
            one of the following conditions must be true:
                1) db_driver is sqlite and args.db_name is a valid path
                2) args.db_conn_string is not None and is valid connection string 
                3) args.db_user, args.db_passwd, args.db_host, and args.db_port are not None
        '''
        assert (args.db_driver == 'sqlite' and path.exists(path.dirname(args.db_name))) or \
            args.db_conn_string is not None or \
            (args.db_user is not None and args.db_passwd is not None \
            and args.db_host is not None and args.db_port is not None), 'Received invalid database config'
        print(args)
