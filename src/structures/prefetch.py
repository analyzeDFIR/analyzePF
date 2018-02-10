# -*- coding: UTF-8 -*-
# prefetch.py
# Noah Rubin
# 02/07/2018

from construct import *

from .general import FILETIME, MFTFileReference

PrefetchFileNameString = CString(encoding='utf16')

PrefetchVersion = Enum(Int32ul, XP=0x11, SEVEN=0x17, EIGHT=0x1a, TEN=0x1e)

PrefetchHeader = Struct(
    'Version'           / PrefetchVersion,
    'RawSignature'      / Const(b'SCCA'),
    Padding(4),
    'FileSize'          / Int32ul,
    'RawExecutableName' / String(60, encoding='utf16'),
    'RawPrefetchHash'   / Int32ul,
    Padding(4)
)

PrefetchTraceChainEntry = Struct(
    'NextEntryIndex'        / Int32ul,
    'TotalBlockLoadCount'   / Int32ul,
    Padding(1),
    'SampleDuration'        / Int8ul,
    Padding(2)
)

PrefetchFileReferences = Struct(
    Padding(4),
    'ReferenceCount'        / Int32ul,
    'References'            / Array(this.ReferenceCount, MFTFileReference)
)

PrefetchDirectoryString = Struct(
    'Length'                / Int16ul,
    'RawString'             / If(this.Length > 0, String(this.Length*2, encoding=StringsAsBytes)),
    Padding(2)
)

'''
Section A: File metrics array
Section B: Trace chains array
Section C: Filename strings
Section D: Volumes information
'''
PrefetchFileInformation17 = Struct(
    'SectionAOffset'        / Int32ul,
    'SectionAEntriesCount'  / Int32ul,
    'SectionBOffset'        / Int32ul,
    'SectionBEntriesCount'  / Int32ul,
    'SectionCOffset'        / Int32ul,
    'SectionCLength'        / Int32ul,
    'SectionDOffset'        / Int32ul,
    'SectionDEntriesCount'  / Int32ul,
    'SectionDLength'        / Int32ul,
    'RawLastExecutionTime'  / Array(1, FILETIME),
    Padding(16),
    'ExecutionCount'        / Int32ul,
    Padding(4)
)

PrefetchFileMetricsEntry17 = Struct(
    'StartTime'             / Int32ul,
    'Duration'              / Int32ul,
    'FileNameOffset'        / Int32ul,
    'FileNameLength'        / Int32ul,
    Padding(4)
)

PrefetchVolumeInformation17 = Struct(
    'VolumeDevicePathOffset'    / Int32ul,
    'VolumeDevicePathLength'    / Int32ul,
    'RawVolumeCreateTime'       / FILETIME,
    'VolumeSerialNumber'        / Int32ul,
    'SectionEOffset'            / Int32ul,
    'SectionELength'            / Int32ul,
    'SectionFOffset'            / Int32ul,
    'SectionFStringsCount'      / Int32ul,
    Padding(4)
)

PrefetchFileInformation23 = Struct(
    'SectionAOffset'        / Int32ul,
    'SectionAEntriesCount'  / Int32ul,
    'SectionBOffset'        / Int32ul,
    'SectionBEntriesCount'  / Int32ul,
    'SectionCOffset'        / Int32ul,
    'SectionCLength'        / Int32ul,
    'SectionDOffset'        / Int32ul,
    'SectionDEntriesCount'  / Int32ul,
    'SectionDLength'        / Int32ul,
    Padding(8),
    'RawLastExecutionTime'     / Array(1, FILETIME),
    Padding(16),
    'ExecutionCount'        / Int32ul,
    Padding(84)
)

PrefetchFileMetricsEntry23 = Struct(
    'StartTime'             / Int32ul,
    'Duration'              / Int32ul,
    'AverageDuration'       / Int32ul,
    'FileNameOffset'        / Int32ul,
    'FileNameLength'        / Int32ul,
    Padding(4),
    'NTFSFileReference'     / MFTFileReference
)

PrefetchVolumeInformation23 = Struct(
    'VolumeDevicePathOffset'    / Int32ul,
    'VolumeDevicePathLength'    / Int32ul,
    'RawVolumeCreateTime'       / FILETIME,
    'VolumeSerialNumber'        / Int32ul,
    'SectionEOffset'            / Int32ul,
    'SectionELength'            / Int32ul,
    'SectionFOffset'            / Int32ul,
    'SectionFStringsCount'      / Int32ul,
    Padding(68)
)

PrefetchFileInformation26 = Struct(
    'SectionAOffset'        / Int32ul,
    'SectionAEntriesCount'  / Int32ul,
    'SectionBOffset'        / Int32ul,
    'SectionBEntriesCount'  / Int32ul,
    'SectionCOffset'        / Int32ul,
    'SectionCLength'        / Int32ul,
    'SectionDOffset'        / Int32ul,
    'SectionDEntriesCount'  / Int32ul,
    'SectionDLength'        / Int32ul,
    Padding(8),
    'RawLastExecutionTime'     / Array(8, FILETIME),
    Padding(16),
    'ExecutionCount'        / Int32ul,
    Padding(96)
)

PrefetchFileMetricsEntry26 = PrefetchFileMetricsEntry23

PrefetchVolumeInformation26 = PrefetchVolumeInformation23

PrefetchFileInformation30 = PrefetchFileInformation26

PrefetchFileMetricsEntry30 = PrefetchFileMetricsEntry26

PrefetchVolumeInformation30 = Struct(
    'VolumeDevicePathOffset'    / Int32ul,
    'VolumeDevicePathLength'    / Int32ul,
    'RawVolumeCreateTime'       / FILETIME,
    'VolumeSerialNumber'        / Int32ul,
    'SectionEOffset'            / Int32ul,
    'SectionELength'            / Int32ul,
    'SectionFOffset'            / Int32ul,
    'SectionFStringsCount'      / Int32ul,
    Padding(60)
)
