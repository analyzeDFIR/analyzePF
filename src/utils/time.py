## -*- coding: UTF-8 -*-
## time.py
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

from datetime import datetime, timezone

class WindowsTime(object):
    '''
    Class for converting raw timestamps in MFT to python DateTime object.
    NTFS MFT time values are 64-bit values representing the number of 
    100-nanosecond intervals since 01/01/1601 00:00:00 UTC. Implementation
    and design inspired by original analyzeMFT (mftutils.WindowsTime)
    '''
    @classmethod
    def parse_mft_filetime(cls, mft_filetime=None, dw_low_datetime=None, dw_high_datetime=None):
        '''
        @WindowsTime.parse
        '''
        return cls(mft_filetime, dw_low_datetime, dw_high_datetime).parse()

    def __init__(self, mft_filetime=None, dw_low_datetime=None, dw_high_datetime=None):
        assert (\
            mft_filetime is not None \
            or (\
                dw_low_datetime is not None \
                and dw_high_datetime is not None\
            )\
        ), 'Please enter either MFTFILETIME struct or low and high values'
        if mft_filetime is not None:
            self._low = int(mft_filetime.dwLowDateTime)
            self._high = int(mft_filetime.dwHighDateTime)
        else:
            self._low = int(dw_low_datetime)
            self._high = int(dw_high_datetime)
    def parse(self):
        '''
        Args:
            N/A
        Returns:
            Python DateTime object of converted MFTFILETIME if no error thrown,
            None otherwise
        Preconditions:
            N/A
        '''
        try:
            return datetime.fromtimestamp( \
                ( float(self._high) * 2 ** 32 + self._low ) * 1e-7 - 11644473600, \
                timezone.utc
            )
        except:
            return None
