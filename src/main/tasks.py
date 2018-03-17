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

class BaseParseTask(object):
    '''
    Base task class
    '''
    NULL = None

    def __init__(self, nodeidx, filepath, **kwargs):
        self.nodeidx = nodeidx
        self.filepath = filepath
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])
    def __call__(self, worker_name):
        pf = Prefetch(self.filepath)
        result_set = self._get_resultset(pf)
        self._handle_resultset(result_set, worker_name)
        return True

class BaseParseFileOutputTask(BaseParseTask):
    '''
    Base task class for writing to output file
    '''
    NULL = ''

    def _get_resultset(self, pf):
        '''
        Args:
            pf: Prefetch    => prefetch file to extract results from 
        Returns:
            List<List<Any>>
            List of results to write to output file
        Preconditions:
            pf is of type Prefetch  (assumed True)
        '''
        raise NotImplementedError('method _get_resultset not implemented for %s'%type(self).__name__)
    def _handle_resultset(self, result_set, worker_name):
        '''
        Args:
            result_set: List<List<Any>> => list of results to write to output file
            worker_name: String         => name of worker process handling task
        Procedure:
            Attempt to write each result in result set to the output file,
            logging any errors that occur
        Preconditions:
            result_set is of type List<List<Any>>   (assumed True)
            worker_name is of type String           (assumed True)
        '''
        target_file = path.join(self.target, '%s_tmp_amft.out'%worker_name)
        try:
            if len(result_set) > 0:
                with open(target_file, 'a') as f:
                    for result in result_set:
                        try:
                            if hasattr(self, 'sep'):
                                f.write(self.sep.join(result) + '\n')
                            else:
                                f.write(result + '\n')
                        except Exception as e:
                            Logger.error('Failed to write %s to output file %s (%s)'%(str(result), target_file, str(e)))
        except Exception as e:
            Logger.error('Failed to write results to output file %s (%s)'%(target_file, str(e)))

class ParseCSVTask(BaseParseFileOutputTask):
    '''
    Task class for parsing single Prefetch file to CSV format
    '''
    def _get_resultset(self, pf):
        '''
        @BaseParseFileOutputTask._get_resultset
        '''
        result_set = list()
        if self.info_type == 'summary':
            try:
                pf.parse()
            except Exception as e:
                Logger.error('Failed to parse Prefetch file %s (%s)'%(self.filepath, str(e)))
            else:
                try:
                    result = [\
                        str(self.nodeidx),
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
                        '|'.join(str(fstring) for fstring in pf.filename_strings),
                        pf.volumes_info.VolumeDevicePath if hasattr(pf.volumes_info, 'VolumeDevicePath') else self.NULL,
                        pf.volumes_info.VolumeCreateTime.strftime('%Y-%m-%d %H:%M:%S.%f%z'),
                        str(pf.volumes_info.VolumeSerialNumber)\
                    ]
                    for attribute_key in ['file_metrics', 'trace_chains', 'file_references', 'directory_strings']:
                        attribute = getattr(pf, attribute_key)
                        result.append(str(len(attribute)) if attribute is not None else self.NULL)
                    result_set.append(result)
                except Exception as e:
                    Logger.error('Failed to create CSV output record (%s)'%str(e))
        return result_set

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

    def _get_resultset(self, pf):
        '''
        @BaseParseFileOutputTask._get_resultset
        '''
        result_set = list()
        try:
            pf.parse()
        except Exception as e:
            Logger.error('Failed to parse Prefetch file %s (%s)'%(self.filepath, str(e)))
        else:
            try:
                if len(pf.file_info.LastExecutionTime) > 0:
                    file_path = path.basename(self.filepath)
                    file_size = stat(self.filepath).st_size
                    for execution_time in pf.file_info.LastExecutionTime:
                        if execution_time.year != 1601:
                            result = [\
                                str(self.nodeidx),
                                self.NULL,
                                self.NULL,
                                file_path,
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
                            result_set.append(result)
            except Exception as e:
                Logger.error('Failed to create BODY output record (%s)'%str(e))
        return result_set

class ParseJSONTask(BaseParseFileOutputTask):
    '''
    Task class for parsing single Prefetch file to JSON format
    '''
    def _get_resultset(self, pf):
        '''
        @BaseParseFileOutputTask._get_resultset
        '''
        result_set = list()
        try:
            pf.parse()
            for idx in range(len(pf.file_info.LastExecutionTime)):
                pf.file_info.LastExecutionTime[idx] = pf.file_info.LastExecutionTime[idx].strftime('%Y-%m-%d %H:%M:%S.%f%z')
            pf.volumes_info.VolumeCreateTime = pf.volumes_info.VolumeCreateTime.strftime('%Y-%m-%d %H:%M:%S.%f%z')
            serializable_entry = Container(**pf)
            result = dumps(serializable_entry, sort_keys=True, indent=(2 if self.pretty else None))
        except Exception as e:
            Logger.error('Failed to parse Prefetch file %s (%s)'%(self.filepath, str(e)))
        else:
            try:
                result_set.append(result)
            except Exception as e:
                Logger.error('Failed to create JSON output record (%s)'%str(e))
        return result_set
