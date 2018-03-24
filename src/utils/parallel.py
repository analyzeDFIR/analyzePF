## -*- coding: UTF-8 -*-
## parallel.py
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
import os
from uuid import uuid4
from multiprocessing import Process, JoinableQueue, RLock, cpu_count
from glob import glob
from heapq import merge as heapq_merge
from tqdm import tqdm

from src.utils.config import initialize_logger

CPU_COUNT = cpu_count()

def coalesce_files(glob_pattern, target, transform=lambda line: line, clean=True):
    '''
    Args:
        glob_pattern: String                    => glob pattern of files to merge
        target: String                          => file path to merge files into
        transform: Callable<String> -> String   => transform to perform on each line
    Procedure:
        Gather all files that match glob_pattern and merge them into target
        **NOTE: assumes each file is sorted and can be naturally sorted by columns
    Preconditions:
        glob_pattern is of type String
        target is of type String
        transform is of type Callable<String> -> String
    '''
    assert isinstance(glob_pattern, str), 'Glob_pattern is not of type String'
    assert isinstance(target, str), 'Target is not of type String'
    assert callable(transform), 'Transform is not of type Callable<String> -> String'
    file_list = glob(glob_pattern)
    if len(file_list) == 0:
        return
    elif len(file_list) == 1 and not os.path.exists(file_list[0]):
        os.rename(file_list[0], target)
    else:
        handle_list = [open(filepath, 'r') for filepath in file_list]
        merged_records = heapq_merge(*[(transform(line) for line in handle) for handle in handle_list])
        try:
            with open(target, 'a') as target_file:
                for record in merged_records:
                    target_file.write(record)
        finally:
            for handle in handle_list:
                handle.close()
            if clean:
                for path in file_list:
                    os.remove(path)

class BaseQueueWorker(Process):
    '''
    Class to spawn worker process with queue of tasks
    '''
    def __init__(self, queue, *args, result_queue=None, name=lambda: str(uuid4()), **kwargs):
        super(BaseQueueWorker, self).__init__(name=name() if callable(name) else name)
        self._queue = queue
        self._result_queue = result_queue
    def _preamble(self):
        '''
        Args:
            N/A
        Procedure:
            Performs worker initialization tasks
        Preconditions:
            N/A
        '''
        return None
    def _result_callback(self):
        '''
        Args:
            N/A
        Procedure:
            Callback when a task is run and worker should continue
        Preconditions:
            N/A
        '''
        return None
    def _closing_callback(self):
        '''
        Args:
            N/A
        Procedure:
            Callback when the worker received a poison pill
        Preconditions:
            N/A
        '''
        return None
    def _process_task(self):
        '''
        Args:
            N/A
        Returns:
            Boolean
            True if worker should continue, false otherwise
        Preconditions:
            N/A
        '''
        raise NotImplementedError('method _process_task not implemented for %s'%type(self).__name__)
    def _postamble(self):
        '''
        Args:
            N/A
        Procedure:
            Performs worker teardown tasks
        Preconditions:
            N/A
        '''
        return None
    def run(self):
        '''
        Args:
            N/A
        Procedure:
            Run the worker, picking tasks off the queue until 
            a poison pill (None) is encountered
        Preconditions:
            N/A
        '''
        self._preamble()
        while True:
            result = self._process_task()
            if not result:
                self._closing_callback()
                break
            self._result_callback()
        self._postamble()

class LoggedQueueWorker(BaseQueueWorker):
    '''
    @BaseQueueWorker
    '''
    def __init__(self, *args, log_path=None, **kwargs):
        super(LoggedQueueWorker, self).__init__(*args, **kwargs)
        self._log_path = log_path
    def _preamble(self):
        '''
        @BaseQueueWorker._preamble
        '''
        if self._log_path is not None:
            initialize_logger(self._log_path, self.name + '_tmp_apf')
            Logger.info('Started worker: ' + self.name)
    def _process_task(self):
        '''
        @BaseQueueWorker._process_task
        '''
        task = self._queue.get()
        try:
            if task is None:
                return False
            result = task(self) if callable(task) else task
            if self._result_queue is not None:
                for entry in result:
                    self._result_queue.put(entry)
            return True
        except Exception as e:
            if self._log_path is not None:
                Logger.error('Uncaught exception while executing %s (%s)'%(type(task).__name__, str(e)))
            if self._result_queue is not None:
                self._result_queue.put(e)
            return True
        finally:
            self._queue.task_done()
    def _postamble(self):
        '''
        @BaseQueueWorker._postamble
        '''
        if self._log_path is not None:
            Logger.info('Ended worker: ' + self.name)

class ProgressTrackerWorker(LoggedQueueWorker):
    '''
    @BaseQueueWorker
    '''
    def __init__(self, *args, pcount=None, pdesc=None, punit=None, **kwargs):
        super(ProgressTrackerWorker, self).__init__(*args, **kwargs)
        self._pcount = pcount
        self._pdesc = pdesc
        self._punit = punit
    def _preamble(self):
        '''
        @BaseQueueWorker._preamble
        '''
        super(ProgressTrackerWorker, self)._preamble()
        self._progress = tqdm(total=self._pcount, desc=self._pdesc, unit=self._punit)
    def _result_callback(self):
        '''
        @BaseQueueWorker._result_callback
        '''
        self._progress.update(1)
    def _closing_callback(self):
        '''
        @BaseQueueWorker._closing_callback
        '''
        self._progress.close()

class DBProgressTrackerWorker(ProgressTrackerWorker):
    '''
    @BaseQueueWorker
    '''
    def __init__(self, *args, manager=None, **kwargs):
        super(DBProgressTrackerWorker, self).__init__(*args, **kwargs)
        self.manager = manager
    def _postamble(self):
        '''
        @BaseQueueWorker._postamble
        '''
        super(DBProgressTrackerWorker, self)._postamble()
        self.manager.close_session()

class WorkerPool(object):
    '''
    Class to manage pool of process workers
    '''
    def __init__(self, task_queue, task_class, daemonize=True, worker_class=LoggedQueueWorker, worker_count=(2 if cpu_count() <= 4 else 4), worker_kwargs=dict(), task_kwargs=dict()):
        self._queue = task_queue
        self._task_class = task_class
        self._worker_class = worker_class
        self._task_kwargs = task_kwargs
        self._worker_kwargs = worker_kwargs
        self._workers = None
        self.daemon = daemonize
        self.worker_count = worker_count
    def __repr__(self):
        return 'WorkerPool(%s,%s worker_class=%s, daemonize=%s, worker_count=%s%s)'%(\
            type(self._queue).__name__ + '()',\
            ' *' + str(self._task_args) + ', ' if len(self._task_args) > 0 else '',\
            type(self._worker_class).__name__,\
            str(self.daemon),\
            str(self.worker_count),\
            ', **' + str(self._task_kwargs) if len(self._task_kwargs) > 0 else '')
    @property
    def queue(self):
        '''
        Args:
            N/A
        Returns:
            JoinableQueue
            Underlying queue of worker pool
        Preconditions:
            N/A
        '''
        return self._queue
    @property
    def worker_kwargs(self):
        '''
        Args:
            N/A
        Returns:
            Dict<String, Any>
            Arguments to be applied to all workers in pool
        Preconditions:
            N/A
        '''
        return self._worker_kwargs
    @worker_kwargs.setter
    def worker_kwargs(self, value):
        '''
        Args:
            N/A
        Procedure:
            Sets arguments to be applied to all workers in pool
        Preconditions:
            value is of type Dict<String, Any>
        '''
        assert isinstance(value, dict), 'Value is not of type Dict<String, Any>'
        self._worker_kwargs = value
    @property
    def task_kwargs(self):
        '''
        Args:
            N/A
        Returns:
            Dict<String, Any>
            Arguments to be applied to all tasks supplied to workers
        Preconditions:
            N/A
        '''
        return self._task_kwargs
    @task_kwargs.setter
    def task_kwargs(self, value):
        '''
        Args:
            N/A
        Procedure:
            Sets arguments to be applied to all tasks supplied to workers
        Preconditions:
            value is of type Dict<String, Any>
        '''
        assert isinstance(value, dict), 'Value is not of type Dict<String, Any>'
        self._task_kwargs = value
    def add_task(self, *args, poison_pill=False, **kwargs):
        '''
        Args:
            N/A
        Procedure:
            Add task to task queue
        Preconditions:
            N/A
        '''
        action = 'put'
        task_args = dict(kwargs)
        task_args.update(self._task_kwargs)
        task = self._task_class(*args, **task_args) if not poison_pill else None
        getattr(self._queue, action)(task)
    def add_poison_pills(self):
        '''
        Args:
            N/A
        Procedure:
            Add poison pill to task queue
        Preconditions:
            N/A
        '''
        for i in range(self.worker_count):
            self.add_task(poison_pill=True)
    def initialize_workers(self):
        '''
        Args:
            N/A
        Procedure:
            Create worker objects in self._workers
        Preconditions:
            N/A
        '''
        self._workers = [\
            self._worker_class(self._queue, i, **self._worker_kwargs)\
            for i in range(self.worker_count)\
        ]
    def start(self):
        '''
        Args:
            N/A
        Procedure:
            Start all worker objects in self._workers
        Preconditions:
            N/A
        '''
        if self._workers is None:
            self.initialize_workers()
        for worker in self._workers:
            if not worker.is_alive():
                worker.daemon = self.daemon
                worker.start()
    def join_tasks(self):
        '''
        Args:
            N/A
        Procedure:
            Join on self._queue if is of type JoinableQueue
        Preconditions:
            N/A
        '''
        if hasattr(self._queue, 'join') and callable(self._queue.join):
            self._queue.join()
    def join_workers(self):
        '''
        Args:
            N/A
        Procedure:
            Join all living worker processes in self._workers
        Preconditions:
            N/A
        '''
        if self._workers is not None:
            for worker in self._workers:
                if worker.is_alive():
                    worker.join()
    def terminate(self):
        '''
        Args:
            N/A
        Procedure:
            Terminate all living worker processes in self._workers
        Preconditions:
            N/A
        '''
        if self._workers is not None:
            for worker in self._workers:
                if worker.is_alive():
                    worker.terminate()
    def refresh(self):
        '''
        Args:
            N/A
        Procedure:
            Terminate all living worker processes and create fresh workers
        Preconditions:
            All worker processes have been killed
        '''
        self._workers = None
        self.initialize_workers()
