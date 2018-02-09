# -*- coding: UTF-8 -*-
# general.py
# Noah Rubin
# 02/07/2018

from src.utils.time import WindowsTime
from construct import *

FILETIME = Struct(
    'dwLowDateTime'     / Int32ul,
    'dwHighDateTime'    / Int32ul
)

MFTFileReference = Struct(
    'SegmentNumber'     / Int32ul,
    Padding(2),
    'SequenceNumber'    / Int16ul
)
