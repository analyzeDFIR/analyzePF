## -*- coding: UTF-8 -*-
## tasks.py
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
from os import path, stat
from datetime import datetime, timezone, timedelta
from json import dumps
from construct import Container

from src.parsers.prefetch import Prefetch
import src.database.models as db

class BaseParseTask(object):
    '''
    Base class for parsing tasks
    '''

    def __init__(self, source):
        self._source = source
        self._resultset = None
    @property
    def source(self):
        '''
        @source.getter
        '''
        return self._source
    @source.setter
    def source(self, value):
        '''
        @source.setter
        Preconditions:
            N/A
        '''
        raise AttributeError('source attribute must be set in the constructor')
    @property
    def resultset(self):
        '''
        @resultset.getter
        '''
        return self._resultset
    @resultset.setter
    def resultset(self, value):
        '''
        @_resultset.setter
        Preconditions:
            value if of type List<Any>
        '''
        assert isinstance(value, list)
        self._resultset = value
    def extract_resultset(self, worker):
        '''
        Args:
            worker: BaseQueueWorker => worker that called this task
        Procedure:
            Convert source into result set
        Preconditions:
            worker is subclass of BaseQueueWorker
        '''
        raise NotImplementedError('extract_resultset method not implemented for %s'%type(self).__name__)
    def process_resultset(self, worker):
        '''
        Args:
            worker: BaseQueueWorker => worker that called this task
        Procedure:
            Process result set created in extract_resultset
        Preconditions:
            worker is subclass of BaseQueueWorker
        '''
        raise NotImplementedError('process_resultset method not implemented for %s'%type(self).__name__)
    def __call__(self, worker):
        '''
        Args:
            worker: BaseQueueWorker => worker that called this task
        Returns:
            Any
            Result of running this task
        Preconditions:
            worker is subclass of BaseQueueWorker
        '''
        self.extract_resultset(worker)
        return self.process_resultset(worker)

class BaseParseFileOutputTask(BaseParseTask):
    '''
    Base class for tasks that write output to file
    '''
    NULL = ''

    def __init__(self, source, nodeidx, **context):
        super(BaseParseFileOutputTask, self).__init__(source)
        self._nodeidx = nodeidx
        if 'target' not in context:
            raise KeyError('target was not provided as a keyword argument')
        self._context = context
    @property
    def nodeidx(self):
        '''
        @nodeidx.getter
        '''
        return self._nodeidx
    @nodeidx.setter
    def nodeidx(self, value):
        '''
        @nodeidx.setter
        Preconditions:
            N/A
        '''
        raise AttributeError('nodeidx attribute must be set in the constructor')
    @property
    def context(self):
        '''
        @context.getter
        '''
        return self._context
    @context.setter
    def context(self, value):
        '''
        @context.setter
        Preconditions:
            value is of type Container
        '''
        if self._context is None:
            assert isinstance(value, Container)
            self._context = value
        else:
            raise AttributeError('context attribute has already been set')
    def process_resultset(self, worker):
        '''
        @BaseParseTask.process_resultset
        '''
        target_file = path.join(self.context.get('target'), '%s_tmp_apf.out'%worker.name)
        try:
            if len(self.result_set) > 0:
                successful_results = 0
                with open(target_file, 'a') as f:
                    for result in self.result_set:
                        try:
                            if 'sep' in self.context:
                                f.write(self.context.get('sep').join(result) + '\n')
                            else:
                                f.write(result + '\n')
                            successful_results += 1
                        except Exception as e:
                            Logger.error('Failed to write result for source file %s (%s)'%(self.source, str(e)))
        except Exception as e:
            Logger.error('Failed to write results for source file %s (%s)'%(self.source, str(e)))
        else:
            Logger.info('Successfully wrote %d result(s) for source file %s'%(successful_results, self.source))
        finally:
            return True

class ParseCSVTask(BaseParseFileOutputTask):
    '''
    Class for parsing single Prefetch file to CSV format
    '''
    def extract_resultset(self, worker):
        '''
        @BaseParseTask.extract_resultset
        '''
        self.result_set = list()
        if self.context.get('info_type') == 'summary':
            try:
                pf = Prefetch(self.source)
                pf.parse()
            except Exception as e:
                Logger.error('Failed to parse Prefetch file %s (%s)'%(self.source, str(e)))
            else:
                try:
                    result = [\
                        str(self.context.get('nodeidx')),
                        str(pf.header.Version),
                        str(pf.header.Signature),
                        str(pf.header.ExecutableName if hasattr(pf.header, 'ExecutableName') else self.NULL),
                        str(pf.header.PrefetchHash if hasattr(pf.header, 'PrefetchHash') else self.NULL),
                        str(pf.file_info.SectionAEntriesCount),
                        str(pf.file_info.SectionBEntriesCount),
                        str(pf.file_info.SectionCLength),
                        str(pf.file_info.SectionDEntriesCount),
                        pf.file_info.LastExecutionTime[0].strftime('%Y-%m-%d %H:%M:%S.%f%z') \
                            if len(pf.file_info.LastExecutionTime) > 0 and pf.file_info.LastExecutionTime[0] is not None \
                            else self.NULL,
                        str(pf.file_info.ExecutionCount),
                        '|'.join([\
                            volumes_info_entry.VolumeDevicePath \
                            if hasattr(volumes_info_entry, 'VolumeDevicePath') else self.NULL \
                            for volumes_info_entry in pf.volumes_info\
                        ]),
                        '|'.join([\
                            volumes_info_entry.VolumeCreateTime.strftime('%Y-%m-%d %H:%M:%S.%f%z') \
                            if hasattr(volumes_info_entry, 'VolumeCreateTime') else self.NULL \
                            for volumes_info_entry in pf.volumes_info\
                        ]),
                        '|'.join([\
                            str(volumes_info_entry.VolumeSerialNumber) \
                            if hasattr(volumes_info_entry, 'VolumeSerialNumber') else self.NULL \
                            for volumes_info_entry in pf.volumes_info\
                        ])\
                    ]
                    for attribute_key in ['file_metrics', 'trace_chains']:
                        attribute = getattr(pf, attribute_key)
                        result.append(str(len(attribute)) if attribute is not None else self.NULL)
                    for attribute_key in ['file_references', 'directory_strings']:
                        attribute = getattr(pf, attribute_key)
                        result.append('|'.join(str(len(attribute_entry)) for attribute_entry in attribute)) 
                    result.append('|'.join(str(fstring) for fstring in pf.filename_strings))
                    self.result_set.append(result)
                except Exception as e:
                    Logger.error('Failed to create CSV output record for source file %s (%s)'%(self.source, str(e)))

class ParseBODYTask(BaseParseFileOutputTask):
    '''
    Task class for parsing single Prefetch file to BODY format
    '''
    @staticmethod
    def to_timestamp(dt):
        '''
        Args:
            dt: DateTime<UTC>   => datetime object to convert
        Returns:
            Float
            Datetime object converted to Unix epoch time
        Preconditions:
            dt is timezone-aware timestamp with timezone UTC
        '''
        return (dt - datetime(1970,1,1, tzinfo=timezone.utc)) / timedelta(seconds=1)

    def extract_resultset(self, worker):
        '''
        @BaseParseTask.extract_resultset
        '''
        self.result_set = list()
        try:
            pf = Prefetch(self.source)
            pf.parse()
        except Exception as e:
            Logger.error('Failed to parse Prefetch file %s (%s)'%(self.source, str(e)))
        else:
            try:
                if len(pf.file_info.LastExecutionTime) > 0:
                    file_name = path.basename(self.source)
                    file_size = stat(self.source).st_size
                    for execution_time in pf.file_info.LastExecutionTime:
                        if execution_time.year != 1601:
                            result = [\
                                str(self.context.get('nodeidx')),
                                self.NULL,
                                self.NULL,
                                file_name,
                                self.NULL,
                                self.NULL,
                                self.NULL,
                                'LET',
                                str(file_size),
                                str(self.to_timestamp(execution_time)),
                                self.NULL,
                                self.NULL,
                                self.NULL\
                            ]
                            self.result_set.append(result)
            except Exception as e:
                Logger.error('Failed to create BODY output record for source file %s (%s)'%(self.source, str(e)))

class ParseJSONTask(BaseParseFileOutputTask):
    '''
    Class for parsing single Prefetch file to JSON format
    '''
    def extract_resultset(self, worker):
        '''
        @BaseParseTask.extract_resultset
        '''
        self.result_set = list()
        try:
            pf = Prefetch(self.source)
            result = dumps(pf.parse().serialize(), sort_keys=True, indent=(2 if self.context.get('pretty') else None))
        except Exception as e:
            Logger.error('Failed to parse Prefetch file %s (%s)'%(self.source, str(e)))
        else:
            try:
                self.result_set.append(result)
            except Exception as e:
                Logger.error('Failed to create JSON output record for source file %s (%s)'%(self.source, str(e)))

class ParseDBTaskStage2(BaseParseTask):
    '''
    Class to push Prefetch file information to database
    '''
    def extract_resultset(self, worker):
        '''
        @BaseParseTask.extract_resultset
        '''
        self.result_set = list()
        for pf in self.source:
            try:
                ledger = db.FileLedger().populate_fields(pf.get_metadata())
            except Exception as e:
                Logger.error('Failed to get metadata from %s (%s)'%(pf._filepath, str(e)))
            else:
                try:
                    ledger.header = db.Header().populate_fields(pf.header)
                except Exception as e:
                    Logger.error('Failed to get header information from %s (%s)'(pf._filepath, str(e)))
                else:
                    try:
                        ledger.header.file_info = db.FileInformation().populate_fields(pf.file_info)
                        for last_execution_time in pf.file_info.LastExecutionTime:
                            try:
                                ledger.header.file_info.last_execution_times.append(\
                                    db.LastExecutionTime(last_execution_time=last_execution_time)\
                                )
                            except Exception as e:
                                Logger.error('Failed to add last execution time entry from %s (%s)'%(pf._filepath, str(e)))
                    except Exception as e:
                        Logger.error('Failed to get file information from %s (%s)'%(pf._filepath, str(e)))
                    else:
                        try:
                            for file_metric, file_name in zip(pf.file_metrics, pf.filename_strings):
                                try:
                                    db_file_metric = db.FileMetric().populate_fields(file_metric)
                                    db_file_metric.file_name = db.FileMetricsName(file_name=file_name)
                                    db_file_metric.file_reference = db.FileReference().populate_fields(file_metric.FileReference)
                                    ledger.header.file_metrics.append(db_file_metric)
                                except Exception as e:
                                    Logger.error('Failed to add file metrics entry from %s (%s)'%(pf._filepath, str(e)))
                        except Exception as e:
                            Logger.error('Failed to get file metrics information from %s (%s)'%(pf._filepath, str(e)))
                        else:
                            try:
                                for trace_chain in pf.trace_chains:
                                    try:
                                        ledger.header.trace_chains.append(\
                                            db.TraceChain().populate_fields(trace_chain)\
                                        )
                                    except Exception as e:
                                        Logger.error('Failed to add trace chains entry from %s (%s)'%(pf._filepath, str(e)))
                            except Exception as e:
                                Logger.error('Failed to get trace chains information from %s (%s)'%(pf._filepath, str(e)))
                            else:
                                try:
                                    for volumes_info, file_references, directory_strings in zip(pf.volumes_info, pf.file_references, pf.directory_strings):
                                        db_volumes_info = db.VolumesInformation().populate_fields(volumes_info)
                                        for file_reference in file_references:
                                            try:
                                                db_volumes_info.file_references.append(\
                                                    db.FileReference().populate_fields(file_reference)\
                                                )
                                            except Exception as e:
                                                Logger.error('Failed to add file reference to volumes info from %s (%s)'%(pf._filepath, str(e)))
                                        for directory_string in directory_strings:
                                            try:
                                                db_volumes_info.directory_strings.append(\
                                                    db.DirectoryString(string=directory_string)\
                                                )
                                            except Exception as e:
                                                Logger.error('Failed to add directory string to volumes info from %s (%s)'%(pf._filepath, str(e)))
                                        ledger.header.volumes_info.append(db_volumes_info)
                                except Exception as e:
                                    Logger.error('Failed to get volumes information from %s (%s)'%(pf._filepath, str(e)))
                                else:
                                    self.result_set.append(ledger)
    def process_resultset(self, worker):
        '''
        @BaseParseTask.process_resultset
        '''
        if worker.manager.session is None:
            worker.manager.create_session()
        for result in self.result_set:
            try:
                worker.manager.add(result)
                worker.manager.commit()
            except Exception as e:
                Logger.error('Failed to commit result to database (%s)'%str(e))
        return True

class ParseDBTaskStage1(BaseParseTask):
    '''
    Task class to parse single Prefetch file in preparation for insertion into DB
    '''
    def extract_resultset(self, worker):
        '''
        @BaseParseTask.extract_resultset
        '''
        self.result_set = list()
        try:
            pf = Prefetch(self.source)
            pf.parse()
        except Exception as e:
            Logger.error('Failed to parse Prefetch file %s (%s)'%(self.source, str(e)))
        else:
            try:
                self.result_set.append(ParseDBTaskStage2(result))
            except Exception as e:
                Logger.error('Failed to create JSON output record for source file %s (%s)'%(self.source, str(e)))
    def process_resultset(self, worker):
        '''
        @BaseParseTask.process_resultset
        '''
        return self.result_set
