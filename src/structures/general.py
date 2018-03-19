## -*- coding: UTF-8 -*-
## general.py
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

from src.utils.time import WindowsTime
from construct import *

'''
For a good discussion of FILETIME objects and filesystem time accounting,
see https://msdn.microsoft.com/en-us/library/windows/desktop/ms724284(v=vs.85).aspx
'''
NTFSFILETIME = Struct(
    'dwLowDateTime'     / Int32ul,
    'dwHighDateTime'    / Int32ul
)

'''
Is actually a MFT_SEGMENT_REFERENCE structure,
see https://msdn.microsoft.com/en-us/library/bb470211(v=vs.85).aspx
for a discussion of this structure
'''
NTFSFileReference = Struct(
    'SegmentNumber'     / Int32ul,
    Padding(2),
    'SequenceNumber'    / Int16ul
)
