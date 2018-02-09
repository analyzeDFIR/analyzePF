# -*- coding: UTF-8 -*-
# parallel.py
# Noah Rubin
# 02/05/2018

from uuid import uuid4
import logging
from multiprocessing import Process, JoinableQueue, cpu_count

from src.utils.config import initialize_logger

class QueueWorker(Process):
    '''
    Class to spawn worker process with queue of tasks
    '''
    def __init__(self, queue, *args, name=lambda: str(uuid4()), **kwargs):
        super(QueueWorker, self).__init__(name=name)
        self._queue = queue
        self._args = args
        self.name = name() if callable(name) else name
        self._kwargs = kwargs
    def __repr__(self):
        return 'QueueWorker(%s,%s name=%s%s)'%(\
            type(self._queue).__name__ + '()',\
            ' *' + str(self._args) + ', ' if len(self._args) > 0 else '',\
            self.name,\
            ', **' + str(self._kwargs) if len(self._kwargs) > 0 else '')
    def run(self):
        '''
        Args:
            N/A
        Procedure:
            Run the worker, picking tasks off the queue until 
            a poison pill is encountered
        Preconditions:
            N/A
        '''
        while True:
            task = self._queue.get()
            self._queue.task_done()
            if task is None:
                break
            try:
                task(*args, **kwargs)
            except Exception as e:
                logging.getLogger(__name__).error('Uncaught exception while executing %s (%s)'%(type(task).__name__, str(e)))

class LoggedQueueWorker(QueueWorker):
    '''
    @QueueWorker
    '''
    def __init__(self, queue, log_path, *args, name=lambda: str(uuid4()), **kwargs):
        super(LoggedQueueWorker, self).__init__(queue, *args, name, **kwargs)
        self._log_path = log_path
    def run(self):
        '''
        @QueueWorker.run
        '''
        initialize_logger(self._log_path, self.name + '_tmp_pmft')
        logging.getLogger(__name__).info('Started worker: ' + self.name)
        super(LoggedQueueWorker, self).run()
        logging.getLogger(__name__).info('Ended worker: ' + self.name)

class WorkerPool(object):
    '''
    Class to manage pool of QueueWorker instances
    '''
    def __init__(self, task_queue, *args, worker_class=QueueWorker, daemonize=True, worker_count=(2 if cpu_count() <= 4 else 4), **kwargs):
        self._worker_class = worker_class
        self._queue = task_queue
        self._task_args = args
        self._task_kwargs = kwargs
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
    def add_task(self, task):
        '''
        Args:
            N/A
        Procedure:
            Add task to task queue
        Preconditions:
            N/A
        '''
        if hasattr(self._queue, 'put_nowait'):
            self._queue.put_nowait(task)
        else:
            self._queue.put(task)
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
            self.add_task(None)
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
                self._worker_class(self._queue, *self._task_args, **self._task_kwargs)\
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
        if isinstance(self._queue, type(JoinableQueue)):
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
