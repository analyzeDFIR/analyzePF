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
from multiprocessing import Process, JoinableQueue, cpu_count
from glob import glob
from heapq import merge as heapq_merge

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

class QueueWorker(Process):
    '''
    Class to spawn worker process with queue of tasks
    '''
    def __init__(self, queue, name=lambda: str(uuid4())):
        super(QueueWorker, self).__init__(name=name() if callable(name) else name)
        self._queue = queue
    def __repr__(self):
        return 'QueueWorker(%s, name=%s)'%(type(self._queue).__name__ + '()', self.name)
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
        while True:
            task = self._queue.get()
            self._queue.task_done()
            if task is None:
                break
            try:
                task(self.name)
            except Exception as e:
                Logger.error('Uncaught exception while executing %s (%s)'%(type(task).__name__, str(e)))

class LoggedQueueWorker(QueueWorker):
    '''
    @QueueWorker
    '''
    def __init__(self, queue, log_path=None, name=lambda: str(uuid4())):
        super(LoggedQueueWorker, self).__init__(queue, name)
        self._log_path = log_path
    def run(self):
        '''
        @QueueWorker.run
        '''
        if self._log_path is not None:
            initialize_logger(self._log_path, self.name + '_tmp_amft')
            Logger.info('Started worker: ' + self.name)
            super(LoggedQueueWorker, self).run()
            Logger.info('Ended worker: ' + self.name)

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
            self._workers = [\
                self._worker_class(self._queue, **self._worker_kwargs)\
                for i in range(self.worker_count)\
            ]
        for worker in self._workers:
            if not worker.is_alive():
                worker.daemon = self.daemon
                worker.start()
        return True
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
        return True
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
        return True
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
