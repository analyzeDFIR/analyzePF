# -*- coding: UTF-8 -*-
# prefetch.py
# Noah Rubin
# 02/08/2017

from datetime import datetime
from io import BytesIO

from .decompress import DecompressWin10
import src.structures.prefetch as pfstructs
from src.utils.time import WindowsTime

class Prefetch(object):
    '''
    Class for parsing Windows prefetch files
    '''
    def __init__(self, filepath, load=True):
        self._stream = None
        self.filepath = filepath
        if load:
            self.parse()
    def _get_version(self):
        '''
        Args:
            N/A
        Returns:
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
    def get_stream(self, persist=False):
        '''
        '''
        stream = open(self.filepath, 'rb') \
            if self._get_version() is not None \
            else BytesIO(DecompressWin10().decompress(self.filepath))
        if persist:
            self._stream = stream
        return stream
    def parse_directory_strings(self, stream=None, volume_info=None):
        '''
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
                    if directory_string_struct.RawString is not None:
                        directory_string_struct.String = directory_string_struct.RawString.replace(b'\x00', b'')
                    directory_strings.append({\
                        'Length': directory_string_struct.Length,\
                        'String': directory_string_struct.String,\
                        }\
                    )
                except:
                    directory_strings.append(None)
            return directory_strings
        finally:
            stream.seek(original_position)
    def parse_file_references(self, stream=None, volume_info=None):
        '''
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
            file_refs = dict(**pfstructs.PrefetchFileReferences.parse_stream(stream))
            file_refs['References'] = list(map(lambda ref: dict(**ref), file_refs['References']))
            return file_refs
        finally:
            stream.seek(original_position)
    def parse_volumes_info(self, stream=None, header=None, file_info=None):
        '''
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
            volume_info = PrefetchVolumeInformation.parse_stream(stream)
            volume_info.VolumeCreateTime = WindowsTime(volume_info.RawVolumeCreateTime).parse()
            stream.seek(0)
            stream.seek(file_info.get('SectionDOffset') + volume_info.get('VolumeDevicePathOffset'))
            volume_info.VolumeDevicePath = pfstructs.String(\
                    volume_info.VolumeDevicePathLength, \
                    encoding='utf8').parse(\
                        stream.read(volume_info.VolumeDevicePathLength*2).replace(b'\x00', b'')\
                    )
            return {key:value for key,value in volume_info.items() if not key.startswith('Raw')}
        finally:
            stream.seek(original_position)
    def parse_filename_strings(self, stream=None, header=None, file_info=None, file_metrics=None):
        '''
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
                trace_chains.append(dict(**pfstructs.PrefetchTraceChainEntry.parse_stream(stream)))
            return trace_chains
        finally:
            stream.seek(original_position)
    def parse_file_metrics(self, stream=None, header=None, file_info=None):
        '''
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
                file_metrics.append(dict(**PrefetchFileMetricsEntry.parse_stream(stream)))
            return file_metrics
        finally:
            stream.seek(original_position)
    def parse_file_info(self, stream=None, header=None):
        '''
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
        return {key:value for key,value in file_info.items() if not key.startswith('Raw')}
    def parse_header(self, stream=None):
        '''
        '''
        if stream is None:
            stream = self._stream
        header = pfstructs.PrefetchHeader.parse_stream(stream)
        header.Signature = header.RawSignature.decode('utf8')
        header.ExecutableName = header.RawExecutableName.split('\x00')[0]
        header.PrefetchHash = hex(header.RawPrefetchHash).replace('0x', '').upper()
        return {key:value for key,value in header.items() if not key.startswith('Raw')}
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
            self.trace_chains = self.parse_trace_chains()
            self.filename_strings = self.parse_filename_strings()
            self.volumes_info = self.parse_volumes_info()
            self.file_references = self.parse_file_references()
            self.directory_strings = self.parse_directory_strings()
        finally:
            try:
                self._stream.close()
            except:
                pass
