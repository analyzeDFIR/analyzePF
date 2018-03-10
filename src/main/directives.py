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
        parallel.coalesce_files(path.join(args.log_path, '*_tmp_amft.log'), log_path)

    def __init__(self, args):
        self.run_directive(args)

class BaseParseFileOutputDirective(BaseDirective):
    '''
    Base class for directives that output results to a file
    '''
    _TASK_CLASS = None

    @classmethod
    def _get_remaining_count(cls, filepath, record_count, max_records):
        '''
        '''
        file_size = stat(filepath).st_size
        if file_size < cls.MFT_RECORD_SIZE:
            return None
        file_records = file_size/cls.MFT_RECORD_SIZE
        remaining_count = max_records - record_count
        return file_records if file_records <= remaining_count else remaining_count
    @classmethod
    def _get_task_kwargs(cls, args, target_parent):
        '''
        '''
        raise NotImplementedError('_get_worker_kwargs not implemented for %s'%cls.__name__)
    @classmethod
    def _get_worker_kwargs(cls, args):
        '''
        '''
        raise NotImplementedError('_get_worker_kwargs not implemented for %s'%cls.__name__)
    @classmethod
    def run(cls, args):
        '''
        @BaseDirective.run
        '''
        assert path.isdir(path.dirname(args.target)), 'Target does not point to existing directory'
        args.target = path.abspath(args.target)
        target_parent = path.dirname(args.target)
        frontier = cls.get_frontier(args.sources)
        frontier_count = len(frontier)
        if frontier_count > 0 and args.count > 0 and cls._TASK_CLASS is not None:
            worker_pool = parallel.WorkerPool(\
                parallel.JoinableQueue(-1), 
                cls._TASK_CLASS, 
                daemonize=False, 
                worker_count=args.threads,
                worker_kwargs=cls._get_worker_kwargs(args),
                task_kwargs=cls._get_task_kwargs(args, target_parent)\
            )
            worker_pool.start()
            record_count = 0
            track_by_records = args.count == sys.maxsize
            with tqdm(total=frontier_count if track_by_records else args.count, desc='Total', unit='files' if track_by_records else 'records') as node_progress:
                for nodeidx, node in enumerate(frontier):
                    Logger.info('Parsing $MFT file %s (node %d)'%(node, nodeidx))
                    mft_file = open(node, 'rb')
                    try:
                        recordidx = 0
                        remaining_count = cls._get_remaining_count(node, record_count, args.count)
                        if remaining_count > 0:
                            with tqdm(total=remaining_count, desc='%d. %s'%(nodeidx, path.basename(node)), unit='records') as record_progress:
                                mft_record = mft_file.read(cls.MFT_RECORD_SIZE)
                                while mft_record != '' and remaining_count > 0:
                                    worker_pool.add_task(nodeidx, recordidx, mft_record)
                                    mft_record = mft_file.read(cls.MFT_RECORD_SIZE)
                                    recordidx += 1
                                    remaining_count -= 1
                                    record_progress.update(1)
                    finally:
                        record_count += (recordidx + 1)
                        mft_file.close()
                    worker_pool.join_tasks()
                    node_progress.update(1 if args.count == sys.maxsize else recordidx)
                    if record_count >= args.count:
                        break
            worker_pool.add_poison_pills()
            worker_pool.join_workers()
            worker_pool.terminate()
            parallel.coalesce_files(path.join(target_parent, '*_tmp_amft.out'), args.target)

class ParseCSVDirective(BaseDirective):
    '''
    '''
    _TASK_CLASS = tasks.ParseCSVTask

class ParseBODYDirective(BaseDirective):
    '''
    '''
    _TASK_CLASS = tasks.ParseBODYTask

class ParseJSONDirective(BaseDirective):
    '''
    '''
    _TASK_CLASS = tasks.ParseJSONTask

class ParseDBDirective(BaseDirective):
    '''
    '''
    pass
