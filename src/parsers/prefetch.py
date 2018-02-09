# -*- coding: UTF-8 -*-
# prefetch.py
# Noah Rubin
# 02/08/2017

from datetime import datetime
from io import BytesIO

from .decompress import DecompressWin10
import src.structures.prefetch as pfstructs
from src.utils.item import PrefetchItem
from src.utils.time import WindowsTime

class Prefetch(object):
    '''
    Class for parsing Windows prefetch files
    '''
    def __init__(self, filepath, load=True):
        self._stream = None
        self._prefetch = PrefetchItem()
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
            volume_info = self.volume_info.get('metadata')
        if volume_info is None:
            return None
        original_position = stream.tell()
        try:
            stream.seek(0)
            stream.seek(volume_info.SectionFOffset)
            return set([pfstructs.PrefetchDirectoryString.parse_stream(stream) \
                    for i in range(volume_info.SectionFStringsCount)])
        finally:
            stream.seek(original_position)
    def parse_file_references(self, stream=None, volume_info=None):
        '''
        '''
        if stream is None:
            stream = self._stream
        if volume_info is None:
            volume_info = self.volume_info.get('metadata')
        if volume_info is None:
            return None
        original_position = stream.tell()
        try:
            stream.seek(0)
            stream.seek(volume_info.SectionEOffset)
            return pfstructs.PrefetchFileReferences.parse_stream(stream)
        finally:
            stream.seek(original_position)
    def parse_volumes_info(self, stream=None, header=None, file_info=None, parse_subs=True):
        '''
        '''
        if stream is None:
            stream = self._stream
        if header is None:
            header = self._prefetch.header
        if file_info is None:
            file_info = self._prefetch.file_info
        if header is None or file_info is None:
            return None
        original_position = stream.tell()
        try:
            stream.seek(0)
            stream.seek(file_info.SectionDOffset)
            if header.Version == 'XP':
                PrefetchVolumeInformation = pfstructs.PrefetchVolumeInformation17
            elif header.Version == 'SEVEN':
                PrefetchVolumeInformation = pfstructs.PrefetchVolumeInformation23
            elif header.Version == 'EIGHT':
                PrefetchVolumeInformation = pfstructs.PrefetchVolumeInformation26
            else:
                PrefetchVolumeInformation = pfstructs.PrefetchVolumeInformation30
            volume_metainfo = PrefetchVolumeInformation.parse_stream(stream)
            volume_info = dict(\
                metadata=volume_metainfo,
                create_time=volume_metainfo.VolumeCreateTime,\
                serial_number=volume_metainfo.VolumeSerialNumber,\
            )
            stream.seek(0)
            stream.seek(volume_metainfo.VolumeDevicePathOffset)
            volume_info.update(\
                device_path=pfstructs.PrefetchFileNameString.parse(\
                    stream.read(volume_metainfo.VolumeDevicePathLength)
                )\
            )
            if parse_subs:
                volume_info.update(\
                    file_references=self.parse_file_references(stream=stream, volume_info=volume_metainfo),\
                    directory_strings=self.parse_directory_strings(stream=stream, volume_info=volume_metainfo)\
                )
            return volume_info
        finally:
            stream.seek(original_position)
    def parse_filename_strings(self, stream=None, header=None, file_info=None, file_metrics=None):
        '''
        '''
        if stream is None:
            stream = self._stream
        if header is None:
            header = self._prefetch.header
        if file_info is None:
            file_info = self._prefetch.file_info
        if file_metrics is None:
            file_metrics = self._prefetch.file_metrics
        if header is None or file_info is None or file_metrics is None:
            return None
        original_position = stream.tell()
        try:
            stream.seek(0)
            stream.seek(file_info.SectionCOffset)
            filename_strings = list()
            for file_metric in file_metrics:
                break
        finally:
            stream.seek(original_position)
    def parse_trace_chains(self, stream=None, header=None, file_info=None):
        '''
        '''
        if stream is None:
            stream = self._stream
        if header is None:
            header = self._prefetch.header
        if file_info is None:
            file_info = self._prefetch.file_info
        if header is None or file_info is None:
            return None
        original_position = stream.tell()
        try:
            stream.seek(0)
            stream.seek(file_info.SectionBOffset)
            return [pfstructs.PrefetchTraceChainEntry.parse_stream(stream) \
                    for i in range(file_info.SectionBEntriesCount)]
        finally:
            stream.seek(original_position)
    def parse_file_metrics(self, stream=None, header=None, file_info=None):
        '''
        '''
        if stream is None:
            stream = self._stream
        if header is None:
            header = self._prefetch.header
        if file_info is None:
            file_info = self._prefetch.file_info
        if header is None or file_info is None:
            return None
        original_position = stream.tell()
        try:
            stream.seek(0)
            stream.seek(file_info.SectionAOffset)
            if header.Version == 'XP':
                PrefetchFileMetricsEntry = pfstructs.PrefetchFileMetricsEntry17
            elif header.Version == 'SEVEN':
                PrefetchFileMetricsEntry = pfstructs.PrefetchFileMetricsEntry23
            elif header.Version == 'EIGHT':
                PrefetchFileMetricsEntry = pfstructs.PrefetchFileMetricsEntry26
            else:
                PrefetchFileMetricsEntry = pfstructs.PrefetchFileMetricsEntry30
            return [PrefetchFileMetricsEntry.parse_stream(stream) \
                    for i in range(file_info.SectionAEntriesCount)]
        finally:
            stream.seek(original_position)
    def parse_file_info(self, stream=None, header=None):
        '''
        '''
        if stream is None:
            stream = self._stream
        if header is None:
            header = self._prefetch.header
        if header.Version == 'XP':
            PrefetchFileInformation = pfstructs.PrefetchFileInformation17
        elif header.Version == 'SEVEN':
            PrefetchFileInformation = pfstructs.PrefetchFileInformation23
        elif header.Version == 'EIGHT':
            PrefetchFileInformation = pfstructs.PrefetchFileInformation26
        else:
            PrefetchFileInformation = pfstructs.PrefetchFileInformation30
        file_info =  PrefetchFileInformation.parse_stream(stream)
        file_info.LastExecutionTime = list(map(lambda ft: WindowsTime(ft).parse(), file_info.RawLastExecutionTime))
        return file_info
    def parse_header(self, stream=None):
        '''
        '''
        if stream is None:
            stream = self._stream
        header = pfstructs.PrefetchHeader.parse_stream(stream)
        header.ExecutableName = header.RawExecutableName.split('\x00')[0]
        header.PrefetchHash = hex(header.RawPrefetchHash).replace('0x', '').upper()
        return header
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
            self._prefetch.header = self.parse_header()
            self._prefetch.file_info = self.parse_file_info()
            self._prefetch.file_metrics = self.parse_file_metrics()
            self._prefetch.trace_chains = self.parse_trace_chains()
            self._prefetch.filename_strings = self.parse_filename_strings()
            self._prefetch.volumes_info = self.parse_volumes_info()
        finally:
            try:
                self._stream.close()
            except:
                pass
