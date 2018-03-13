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
from os import path
from json import dumps
from construct import Container

from src.parsers.prefetch import Prefetch

class BaseParseTask(object):
    '''
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

class BaseParseFileOutputTask(BaseParseTask):
    '''
    '''
    NULL = ''

    def _handle_resultset(self, result_set, worker_name):
        '''
        '''
        target_file = path.join(self.target, '%s_tmp_amft.out'%worker_name)
        try:
            if len(result_set) > 0:
                with open(target_file, 'a') as f:
                    for result in result_set:
                        try:
                            f.write(self.sep.join(result) + '\n')
                        except Exception as e:
                            Logger.error('Failed to write %s to output file %s (%s)'%(str(result), target_file, str(e)))
        except Exception as e:
            Logger.error('Failed to write results to output file %s (%s)'%(target_file, str(e)))

class ParseCSVTask(BaseParseFileOutputTask):
    '''
    '''
    def _get_resultset(self, pf):
        result_set = list()
        if self.info_type == 'summary':
            try:
                pf.parse()
            except Exception as e:
                Logger.error('Failed to parse Prefetch file %s (%s)'%(self.filepath, str(e)))
            else:
                # FIELDS: Version Signature ExecutableName PrefetchHash
                #         SectionAEntriesCount SectionBEntriesCount SectionCLength SectionDEntriesCount
                #         LastExecutionTime ExecutionCount FileNameStrings
                #         VolumeDevicePath VolumeCreateTime VolumeSerialNumber
                #         FileMetricsCount TraceChainsAccount FileReferenceCount DirectoryStringCount 
                try:
                    result = list()
                    result.append(str(self.nodeidx))
                    result.append(str(pf.header.Version))
                    result.append(str(pf.header.Signature))
                    result.append(str(pf.header.ExecutableName if hasattr(pf.header, 'ExecutableName') else self.NULL))
                    result.append(str(pf.header.PrefetchHash if hasattr(pf.header, 'PrefetchHash') else self.NULL))
                    result.append(str(pf.file_info.SectionAEntriesCount))
                    result.append(str(pf.file_info.SectionBEntriesCount))
                    result.append(str(pf.file_info.SectionCLength))
                    result.append(str(pf.file_info.SectionDEntriesCount))
                    result.append(pf.file_info.LastExecutionTime[0].strftime('%Y-%m-%d %H:%M:%S.%f%z') \
                        if len(pf.file_info.LastExecutionTime) > 0 and pf.file_info.LastExecutionTime[0] is not None \
                        else self.NULL)
                    result.append(str(pf.file_info.ExecutionCount))
                    result.append('|'.join(str(fstring) for fstring in pf.filename_strings))
                    result.append(pf.volumes_info.VolumeDevicePath if hasattr(pf.volumes_info, 'VolumeDevicePath') else self.NULL)
                    result.append(pf.volumes_info.VolumeCreateTime.strftime('%Y-%m-%d %H:%M:%S.%f%z'))
                    result.append(str(pf.volumes_info.VolumeSerialNumber))
                    for attribute_key in ['file_metrics', 'trace_chains', 'file_references', 'directory_strings']:
                        attribute = getattr(pf, attribute_key)
                        result.append(str(len(attribute)) if attribute is not None else self.NULL)
                    result_set.append(result)
                except Exception as e:
                    Logger.error('Failed to create CSV output record (%s)'%str(e))
        return result_set

class ParseBODYTask(BaseParseFileOutputTask):
    '''
    '''
    pass

class ParseJSONTask(BaseParseFileOutputTask):
    '''
    '''
    pass
