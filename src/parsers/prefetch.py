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

from io import BytesIO
from construct.lib import Container

from .decompress import DecompressWin10
import src.structures.prefetch as pfstructs
from src.utils.time import WindowsTime
from src.utils.item import BaseItem, Field

class Prefetch(BaseItem):
    '''
    Class for parsing Windows prefetch files
    '''
    header              = Field(1)
    file_info           = Field(2)
    file_metrics        = Field(3)
    trace_chains        = Field(4)
    filename_strings    = Field(5)
    volumes_info        = Field(6)
    file_references     = Field(7)
    directory_Strings   = Field(8)

    def __init__(self, filepath, load=False):
        super(Prefetch, self).__init__()
        self._stream = None
        self.filepath = filepath
        if load:
            self.parse()
    def _get_version(self):
        '''
        Args:
            N/A
        Returns:
            ByteString
            Prefetch version if successful, None otherwise
        Preconditions:
            N/A
        '''
        with open(self.filepath, 'rb') as pf:
            try:
                version = pfstructs.PrefetchVersion.parse_stream(pf)
            except:
                version = None
        return version
    def _clean_transform(self, value):
        '''
        Args:
            value: Any  => value to be converted
        Returns:
            Any
            Raw value if it is not of type Container, else recursively removes
            any key beginning with 'Raw'
        Preconditions:
            N/A
        '''
        if issubclass(type(value), Container):
            cleaned_value = Container(value)
            for key in cleaned_value.keys():
                if key.startswith('Raw'):
                    del cleaned_value[key]
                else:
                    cleaned_value[key] = self._clean_transform(cleaned_value[key])
            return cleaned_value
        else:
            return value
    def get_stream(self, persist=False):
        '''
        Args:
            persist: Boolean    => whether to persist stream as attribute on self
        Returns:
             TextIOWrapper|BytesIO
            Stream of prefetch file at self.filepath
        Preconditions:
            persist is of type Boolean  (assumed True)
        '''
        stream = open(self.filepath, 'rb') \
            if self._get_version() is not None \
            else BytesIO(DecompressWin10().decompress(self.filepath))
        if persist:
            self._stream = stream
        return stream
    def parse_directory_strings(self, stream=None, volume_info=None):
        '''
        Args:
            stream: TextIOWrapper|BytesIO   => stream to read from
            volume_info: Container          => volumes information parsed from stream
        Returns:
            List<Container<String, Integer|String>>
            List of directory strings and their lengths
        Preconditions:
            stream is of type TextIOWrapper or BytesIO  (assumedTrue)
            volume_info is of type Container            (assumedTrue)
        '''
        if stream is None:
            stream = self._stream
        if volume_info is None:
            volume_info = self.volumes_info
        if volume_info is None:
            return None
        original_position = stream.tell()
        try:
            stream.seek(0)
            stream.seek(volume_info.get('SectionFOffset'))
            directory_strings = list()
            for i in range(volume_info.get('SectionFStringsCount')):
                try:
                    directory_string_struct = pfstructs.PrefetchDirectoryString.parse_stream(stream)
                    directory_string_struct.String = stream.read(directory_string_struct.Length * 2 + 2)
                    directory_strings.append(Container(\
                        Length=directory_string_struct.Length,
                        String=directory_string_struct.String\
                        )\
                    )
                except:
                    directory_strings.append(None)
            return directory_strings
        finally:
            stream.seek(original_position)
    def parse_file_references(self, stream=None, volume_info=None):
        '''
        Args:
            stream: TextIOWrapper|BytesIO   => stream to read from
            volume_info: Container          => volumes information parsed from stream
        Returns:
            List<Container<String, Any>>
            List of file references (see: src.structures.prefetch.PrefetchFileReferences)
        Preconditions:
            stream is of type TextIOWrapper or BytesIO  (assumedTrue)
            volume_info is of type Container            (assumedTrue)
        '''
        if stream is None:
            stream = self._stream
        if volume_info is None:
            volume_info = self.volumes_info
        if volume_info is None:
            return None
        original_position = stream.tell()
        try:
            stream.seek(0)
            stream.seek(volume_info.get('SectionEOffset'))
            file_refs = self._clean_transform(pfstructs.PrefetchFileReferences.parse_stream(stream))
            file_refs['References'] = list(map(lambda ref: Container(**ref), file_refs['References']))
            return file_refs
        finally:
            stream.seek(original_position)
    def parse_volumes_info(self, stream=None, header=None, file_info=None):
        '''
        Args:
            stream: TextIOWrapper|BytesIO   => stream to read from
            header: Container               => prefetch file header information parsed from stream
            file_info: Container            => file information parsed from stream
        Returns:
            List<Container<String, Any>>
            Prefetch file volumes information (see src.structures.prefetch.PrefetchVolumeInformation*)
        Preconditions:
            stream is of type TextIOWrapper or BytesIO  (assumedTrue)
            header is of type Container                 (assumedTrue)
            file_info is of type Container              (assumedTrue)
        '''
        if stream is None:
            stream = self._stream
        if header is None:
            header = self.header
        if file_info is None:
            file_info = self.file_info
        if header is None or file_info is None:
            return None
        original_position = stream.tell()
        try:
            stream.seek(0)
            stream.seek(file_info.get('SectionDOffset'))
            if header.get('Version') == 'XP':
                PrefetchVolumeInformation = pfstructs.PrefetchVolumeInformation17
            elif header.get('Version') == 'SEVEN':
                PrefetchVolumeInformation = pfstructs.PrefetchVolumeInformation23
            elif header.get('Version') == 'EIGHT':
                PrefetchVolumeInformation = pfstructs.PrefetchVolumeInformation26
            else:
                PrefetchVolumeInformation = pfstructs.PrefetchVolumeInformation30
            volumes_info_list = list()
            for i in range(file_info.SectionDEntriesCount):
                volumes_info = PrefetchVolumeInformation.parse_stream(stream)
                volumes_info_position = stream.tell()
                volumes_info.VolumeCreateTime = WindowsTime(volumes_info.RawVolumeCreateTime).parse()
                stream.seek(file_info.get('SectionDOffset') + volumes_info.get('VolumeDevicePathOffset'))
                volumes_info.VolumeDevicePath = pfstructs.String(\
                        volumes_info.VolumeDevicePathLength, \
                        encoding='utf8').parse(\
                            stream.read(volumes_info.VolumeDevicePathLength*2).replace(b'\x00', b'')\
                        )
                volumes_info_list.append(volumes_info)
                stream.seek(volumes_info_position)
            return self._clean_transform(volumes_info_list)
        finally:
            stream.seek(original_position)
    def parse_filename_strings(self, stream=None, header=None, file_info=None, file_metrics=None):
        '''
        Args:
            stream: TextIOWrapper|BytesIO   => stream to read from
            header: Container               => prefetch file header information parsed from stream
            file_info: Container            => file information parsed from stream
            file_metrics: Container         => file metrics array parsed from stream
        Returns:
            List<String>
            List of filename strings associated with file_metrics array
        Preconditions:
            stream is of type TextIOWrapper or BytesIO  (assumedTrue)
            header is of type Container                 (assumedTrue)
            file_info is of type Container              (assumedTrue)
            file_metrics is of type Container           (assumedTrue)
        '''
        if stream is None:
            stream = self._stream
        if header is None:
            header = self.header
        if file_info is None:
            file_info = self.file_info
        if file_metrics is None:
            file_metrics = self.file_metrics
        if header is None or file_info is None or file_metrics is None:
            return None
        original_position = stream.tell()
        try:
            stream.seek(0)
            stream.seek(file_info.get('SectionCOffset'))
            filename_strings = list()
            for file_metric in file_metrics:
                if (stream.tell() - file_info.get('SectionCOffset')) <= file_info.get('SectionCLength'):
                    filename_strings.append(\
                        pfstructs.PrefetchFileNameString.parse_stream(stream)\
                    )
                else:
                    filename_strings.append(None)
            return filename_strings
        finally:
            stream.seek(original_position)
    def parse_trace_chains(self, stream=None, header=None, file_info=None):
        '''
        Args:
            stream: TextIOWrapper|BytesIO   => stream to read from
            header: Container               => prefetch file header information parsed from stream
            file_info: Container            => file information parsed from stream
        Returns:
            List<Container<String, Any>>
            Prefetch file trace chains information array (see: src.structures.prefetch.PrefetchTraceChainEntry)
        Preconditions:
            stream is of type TextIOWrapper or BytesIO  (assumedTrue)
            header is of type Container                 (assumedTrue)
            file_info is of type Container              (assumedTrue)
        '''
        if stream is None:
            stream = self._stream
        if header is None:
            header = self.header
        if file_info is None:
            file_info = self.file_info
        if header is None or file_info is None:
            return None
        original_position = stream.tell()
        try:
            stream.seek(0)
            stream.seek(file_info.get('SectionBOffset'))
            trace_chains = list()
            for i in range(file_info.get('SectionBEntriesCount')):
                trace_chains.append(self._clean_transform(pfstructs.PrefetchTraceChainEntry.parse_stream(stream)))
            return trace_chains
        finally:
            stream.seek(original_position)
    def parse_file_metrics(self, stream=None, header=None, file_info=None):
        '''
        Args:
            stream: TextIOWrapper|BytesIO   => stream to read from
            header: Container               => prefetch file header information parsed from stream
            file_info: Container            => file information parsed from stream
        Returns:
            List<Container<String, Any>>
            Prefetch file metrics information array (see: src.structures.prefetch.PrefetchFileMetrics*)
        Preconditions:
            stream is of type TextIOWrapper or BytesIO  (assumedTrue)
            header is of type Container                 (assumedTrue)
            file_info is of type Container              (assumedTrue)
        '''
        if stream is None:
            stream = self._stream
        if header is None:
            header = self.header
        if file_info is None:
            file_info = self.file_info
        if header is None or file_info is None:
            return None
        original_position = stream.tell()
        try:
            stream.seek(0)
            stream.seek(file_info.get('SectionAOffset'))
            if header.get('Version') == 'XP':
                PrefetchFileMetricsEntry = pfstructs.PrefetchFileMetricsEntry17
            elif header.get('Version') == 'SEVEN':
                PrefetchFileMetricsEntry = pfstructs.PrefetchFileMetricsEntry23
            elif header.get('Version') == 'EIGHT':
                PrefetchFileMetricsEntry = pfstructs.PrefetchFileMetricsEntry26
            else:
                PrefetchFileMetricsEntry = pfstructs.PrefetchFileMetricsEntry30
            file_metrics = list()
            for i in range(file_info.get('SectionAEntriesCount')):
                file_metrics_entry = self._clean_transform(PrefetchFileMetricsEntry.parse_stream(stream))
                if hasattr(file_metrics_entry, 'FileReference'):
                    file_metrics_entry.FileReference = self._clean_transform(file_metrics_entry.FileReference)
                file_metrics.append(file_metrics_entry)
            return file_metrics
        finally:
            stream.seek(original_position)
    def parse_file_info(self, stream=None, header=None):
        '''
        Args:
            stream: TextIOWrapper|BytesIO   => stream to read from
            header: Container               => prefetch file header information parsed from stream
        Returns:
            Container<String, Any>
            Prefetch file information (see src.structures.prefetch.PrefetchFileInformation*)
        Preconditions:
            stream is of type TextIOWrapper or BytesIO  (assumedTrue)
            header is of type Container                 (assumedTrue)
        '''
        if stream is None:
            stream = self._stream
        if header is None:
            header = self.header
        if header.get('Version') == 'XP':
            PrefetchFileInformation = pfstructs.PrefetchFileInformation17
        elif header.get('Version') == 'SEVEN':
            PrefetchFileInformation = pfstructs.PrefetchFileInformation23
        elif header.get('Version') == 'EIGHT':
            PrefetchFileInformation = pfstructs.PrefetchFileInformation26
        else:
            PrefetchFileInformation = pfstructs.PrefetchFileInformation30
        file_info =  PrefetchFileInformation.parse_stream(stream)
        file_info.LastExecutionTime = list(map(lambda ft: WindowsTime(ft).parse(), file_info.RawLastExecutionTime))
        return self._clean_transform(file_info)
    def parse_header(self, stream=None):
        '''
        Args:
            stream: TextIOWrapper|BytesIO   => stream to read from
        Returns:
            Container<String, Any>
            Prefetch file header information (see src.structures.prefetch.PrefetchHeader)
        Preconditions:
            stream is of type TextIOWrapper or BytesIO  (assumedTrue)
        '''
        if stream is None:
            stream = self._stream
        header = pfstructs.PrefetchHeader.parse_stream(stream)
        header.Signature = header.RawSignature.decode('utf8')
        header.ExecutableName = header.RawExecutableName.split('\x00')[0]
        header.PrefetchHash = hex(header.RawPrefetchHash).replace('0x', '').upper()
        return self._clean_transform(header)
    def parse(self):
        '''
        Args:
            N/A
        Procedure:
            Attempt to parse the supplied prefetch file, extracting
            header, file information, file metrics, trace chains,
            filename strings, and volumes information
        Preconditions:
            self.filepath points to valid prefetch file
        '''
        self._stream = self.get_stream()
        try:
            self.header = self.parse_header()
            self.file_info = self.parse_file_info()
            self.file_metrics = self.parse_file_metrics()
            self.filename_strings = self.parse_filename_strings()
            self.trace_chains = self.parse_trace_chains()
            self.volumes_info = self.parse_volumes_info()
            self.file_references = self.parse_file_references()
            self.directory_strings = self.parse_directory_strings()
        finally:
            try:
                self._stream.close()
            except:
                pass
