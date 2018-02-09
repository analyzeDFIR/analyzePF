# -*- coding: UTF-8 -*-
# time.py
# Noah Rubin
# 02/05/2018

from datetime import datetime

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
            return datetime.utcfromtimestamp(\
                ( float(self._high) * 2 ** 32 + self._low ) * 1e-7 - 11644473600\
            )
        except:
            raise
            return None
