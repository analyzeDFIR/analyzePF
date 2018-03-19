## -*- coding: UTF-8 -*-
## prefetch.py
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

from construct import *

from .general import NTFSFILETIME, NTFSFileReference

PrefetchFileNameString = CString(encoding='utf16')

'''
Prefetch Version: prefetch file format version
    XP      => 0x11 (XP, 2003)
    SEVEN   => 0x17 (Vista, 7)
    EIGHT   => 0x1a (8, 8.1)
    TEN     => 0x1e (10)
'''
PrefetchVersion = Enum(Int32ul, XP=0x11, SEVEN=0x17, EIGHT=0x1a, TEN=0x1e)

'''
Prefetch Header: header of prefetch file
    Version: version of prefetch file format (see: PrefetchVersion)
    RawSignature: prefetch file signature (should always be SCCA)
    FileSize: size of prefetch file in bytes, including header
    RawExecutableName: name of the executable associated with prefetch file
    RawPrefetchHash: prefetch hash of the executable associated with prefetch file
'''
PrefetchHeader = Struct(
    'Version'           / PrefetchVersion,
    'RawSignature'      / Const(b'SCCA'),
    Padding(4),
    'FileSize'          / Int32ul,
    'RawExecutableName' / String(60, encoding='utf16'),
    'RawPrefetchHash'   / Int32ul,
    Padding(4)
)

'''
Prefetch Trace Chain Entry: trace chain array entry
    NextEntryIndex: next index in trace chain array (0 is start, -1 is end)
    TotalBlockLoadCount: total count of blocks loaded, where block size is 512KB
    SampleDuration: Unknown, but suggested to be sample duration in milliseconds
'''
PrefetchTraceChainEntry = Struct(
    'NextEntryIndex'        / Int32ul,
    'TotalBlockLoadCount'   / Int32ul,
    Padding(1),
    'SampleDuration'        / Int8ul,
    Padding(2)
)

'''
Prefetch File References: reference to files associated with executable
    ReferenceCount: number of file references
    References: array of file references (see: NTFSFileReference)
'''
PrefetchFileReferences = Struct(
    Padding(4),
    'ReferenceCount'        / Int32ul,
    'References'            / Array(this.ReferenceCount, NTFSFileReference)
)

'''
Prefetch File Information: metadata about information stored in prefetch file
    Section A: File metrics array
    Section B: Trace chains array
    Section C: Filename strings
    Section D: Volumes information
    RawLastExecutionTime: array of NTFSFILETIME objects
    ExecutionCount: number of times executable has been run
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
    'RawLastExecutionTime'  / Array(1, NTFSFILETIME),
    Padding(16),
    'ExecutionCount'        / Int32ul,
    Padding(4)
)

'''
Prefetch File Metrics Entry: file loading metrics of files associated with executable
    StartTime: prefetch start time in milliseconds
    Duration: prefetch duration time in milliseconds
    FileNameOffset: offset to filename associated with these metrics
    FileNameLength: length of filename associated with these metrics
'''
PrefetchFileMetricsEntry17 = Struct(
    'StartTime'             / Int32ul,
    'Duration'              / Int32ul,
    'FileNameOffset'        / Int32ul,
    'FileNameLength'        / Int32ul,
    Padding(4)
)

'''
Prefetch Volume Information: information about volume executable was sourced from
    VolumeDevicePathOffset: offset to volume device path in bytes (relative to
                            beginning of volumes information section)
    VolumeDevicePathLength: length of volume device path (in UTF16le)
    RawVolumeCreateTime: FILETIME object containing volume creation time
    VolumeSerialNumber: volume serial number taken from volume string
    SectionEOffset: offset to file references section in bytes (relative to
                    beginning of volumes information section)
    SectionELength: length of file references section
    SectionFOffset: offset to directory strings section in bytes (relative to
                    beginning of volumes information section)
    SectionFStringsCount: number of strings in directory strings section
'''
PrefetchVolumeInformation17 = Struct(
    'VolumeDevicePathOffset'    / Int32ul,
    'VolumeDevicePathLength'    / Int32ul,
    'RawVolumeCreateTime'       / NTFSFILETIME,
    'VolumeSerialNumber'        / Int32ul,
    'SectionEOffset'            / Int32ul,
    'SectionELength'            / Int32ul,
    'SectionFOffset'            / Int32ul,
    'SectionFStringsCount'      / Int32ul,
    Padding(4)
)

'''
@PrefetchFileInformation17
'''
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
    'RawLastExecutionTime'  / Array(1, NTFSFILETIME),
    Padding(16),
    'ExecutionCount'        / Int32ul,
    Padding(84)
)

'''
@PrefetchFileMetricsEntry17
    AverageDuration: potentially the average duration in milliseconds
    FileReference: reference to file in MFT that the metrics are associated with
'''
PrefetchFileMetricsEntry23 = Struct(
    'StartTime'             / Int32ul,
    'Duration'              / Int32ul,
    'AverageDuration'       / Int32ul,
    'FileNameOffset'        / Int32ul,
    'FileNameLength'        / Int32ul,
    Padding(4),
    'FileReference'         / NTFSFileReference
)

'''
@PrefetchVolumeInformation17
'''
PrefetchVolumeInformation23 = Struct(
    'VolumeDevicePathOffset'    / Int32ul,
    'VolumeDevicePathLength'    / Int32ul,
    'RawVolumeCreateTime'       / NTFSFILETIME,
    'VolumeSerialNumber'        / Int32ul,
    'SectionEOffset'            / Int32ul,
    'SectionELength'            / Int32ul,
    'SectionFOffset'            / Int32ul,
    'SectionFStringsCount'      / Int32ul,
    Padding(68)
)

'''
@PrefetchFileInformation17
'''
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
    'RawLastExecutionTime'  / Array(8, NTFSFILETIME),
    Padding(16),
    'ExecutionCount'        / Int32ul,
    Padding(96)
)

PrefetchFileMetricsEntry26 = PrefetchFileMetricsEntry23

PrefetchVolumeInformation26 = PrefetchVolumeInformation23

PrefetchFileInformation30 = PrefetchFileInformation26

PrefetchFileMetricsEntry30 = PrefetchFileMetricsEntry26

'''
@PrefetchVolumeInformation17
'''
PrefetchVolumeInformation30 = Struct(
    'VolumeDevicePathOffset'    / Int32ul,
    'VolumeDevicePathLength'    / Int32ul,
    'RawVolumeCreateTime'       / NTFSFILETIME,
    'VolumeSerialNumber'        / Int32ul,
    'SectionEOffset'            / Int32ul,
    'SectionELength'            / Int32ul,
    'SectionFOffset'            / Int32ul,
    'SectionFStringsCount'      / Int32ul,
    Padding(60)
)
