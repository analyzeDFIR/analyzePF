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

    def __init__(self, nodeidx, recordidx, mft_record, **kwargs):
        self.nodeidx = nodeidx
        self.recordidx = recordidx
        self.mft_record = mft_record
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])
    def __call__(self, worker_name):
        mft_entry = MFTEntry(self.mft_record)
        result_set = self._get_resultset(mft_entry)
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
    pass

class ParseBODYTask(BaseParseFileOutputTask):
    '''
    '''
    pass

class ParseJSONTask(BaseParseFileOutputTask):
    '''
    '''
    pass
