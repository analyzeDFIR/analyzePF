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

import logging
Logger = logging.getLogger(__name__)
from os import path
from io import BytesIO
import inspect
from construct.lib import Container
import hashlib
from datetime import datetime
from dateutil.tz import tzlocal, tzutc

from .decompress import DecompressWin10
import src.structures.prefetch as pfstructs
from src.utils.time import WindowsTime

class Prefetch(Container):
    '''
    Class for parsing Windows prefetch files
    '''

    def __init__(self, filepath, load=False):
        super(Prefetch, self).__init__()
        self._stream = None
        self._filepath = filepath
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
        with open(self._filepath, 'rb') as pf:
            try:
                version = pfstructs.PrefetchVersion.parse_stream(pf)
            except:
                version = None
        return version
    def _clean_transform(self, value, serialize=False):
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
                if key.startswith('Raw') or key.startswith('_'):
                    del cleaned_value[key]
                else:
                    cleaned_value[key] = self._clean_transform(cleaned_value[key], serialize)
            return cleaned_value
        elif isinstance(value, list):
            return list(map(lambda entry: self._clean_transform(entry, serialize), value))
        elif isinstance(value, datetime) and serialize:
            return value.strftime('%Y-%m-%d %H:%M:%S.%f%z')
        else:
            return value
    def _prepare_kwargs(self, structure_parser, **kwargs):
        '''
        Args:
            structure_parser: Callable  => function to prepare kwargs for
            kwargs: Dict<String, Any>   => kwargs to prepare
        Returns:
            Dict<String, Any>
            Same set of keyword arguments but with values filled in
            for kwargs supplied as None with attribute values from self
            NOTE:
                This function uses the inspect module to get the keyword
                arguments for the given structure parser.  I know this is weird
                and non-standard OOP, and is subject to change int the future,
                but it works as a nice abstraction on the various structure parsers 
                for now.
        Preconditions:
            structure_parser is callable that takes 0 or more keyword arguments
            Only keyword arguments supplied to function
        '''
        argspec = inspect.getargspec(structure_parser)
        kwargs_keys = argspec.args[(len(argspec.args) - len(argspec.defaults))+1:]
        prepared_kwargs = dict()
        for key in kwargs_keys:
            if key in kwargs:
                if kwargs[key] is None:
                    prepared_kwargs[key] = getattr(\
                        self, 
                        key if key != 'stream' else '_stream', 
                        None\
                    )
                    if prepared_kwargs[key] is None:
                        raise Exception('Attribute %s was no provided and has not been parsed'%key)
                else:
                    prepared_kwargs[key] = kwargs[key]
            else:
                prepared_kwargs[key] = getattr(\
                    self, 
                    key if key != 'stream' else '_stream', 
                    None\
                )
        return prepared_kwargs
    def _parse_directory_strings(self, original_position, stream=None, file_info=None, volumes_info=None):
        '''
        Args:
            original_position: Integer                  => position in stream before parsing this structure
            stream: TextIOWrapper|BytesIO               => stream to read from
            file_info: Container                        => file information parsed from stream
            volumes_info: List<Container<String, Any>>  => volumes information parsed from stream
        Returns:
            List<Container<String, Integer|String>>
            List of directory strings and their lengths
        Preconditions:
            original_position is of type Integer                (assumed True)
            stream is of type TextIOWrapper or BytesIO          (assumed True)
            file_info is of type Container                      (assumed True)
            volume_info is of type List<Container<String, Any>> (assumed True)
        '''
        try:
            directory_strings = list()
            for volumes_info_entry in volumes_info:
                directory_strings_entry = list()
                stream.seek(file_info.SectionDOffset + volumes_info_entry.SectionFOffset)
                for i in range(volumes_info_entry.SectionFStringsCount):
                    try:
                        directory_string_length = pfstructs.Int16ul.parse_stream(stream)
                        directory_string = stream.read(directory_string_length * 2 + 2).decode('UTF16')
                        directory_strings_entry.append(directory_string.strip('\x00'))
                    except Exception as e:
                        Logger.error('Error parsing directory strings entry (%s)'%str(e))
                        directory_strings_entry.append(None)
                directory_strings.append(directory_strings_entry)
            return self._clean_transform(directory_strings)
        finally:
            stream.seek(original_position)
    def _parse_file_references(self, original_position, stream=None, file_info=None, volumes_info=None):
        '''
        Args:
            original_position: Integer                  => position in stream before parsing this structure
            stream: TextIOWrapper|BytesIO               => stream to read from
            file_info: Container                        => file information parsed from stream
            volumes_info: List<Container<String, Any>>  => volumes information parsed from stream
        Returns:
            List<Container<String, Any>>
            List of file references (see: src.structures.prefetch.PrefetchFileReferences)
        Preconditions:
            original_position is of type Integer                (assumed True)
            stream is of type TextIOWrapper or BytesIO          (assumed True)
            file_info is of type Container                      (assumed True)
            volume_info is of type List<Container<String, Any>> (assumed True)
        '''
        try:
            file_refs = list()
            for volumes_info_entry in volumes_info:
                try:
                    stream.seek(file_info.SectionDOffset + volumes_info_entry.SectionEOffset)
                    file_refs_entry = pfstructs.PrefetchFileReferences.parse_stream(stream)
                    file_refs_entry.References = list(map(lambda ref: Container(**ref), file_refs_entry.References))
                    file_refs.append(file_refs_entry)
                except Exception as e:
                    Logger.error('Error parsing file_refs_entry (%s)'%str(e))
                    file_refs.append(None)
            return self._clean_transform(file_refs)
        finally:
            stream.seek(original_position)
    def _parse_volumes_info(self, original_position, stream=None, header=None, file_info=None):
        '''
        Args:
            original_position: Integer      => position in stream before parsing this structure
            stream: TextIOWrapper|BytesIO   => stream to read from
            header: Container               => prefetch file header information parsed from stream
            file_info: Container            => file information parsed from stream
        Returns:
            List<Container<String, Any>>
            Prefetch file volumes information (see src.structures.prefetch.PrefetchVolumeInformation*)
        Preconditions:
            original_position is of type Integer        (assumed True)
            stream is of type TextIOWrapper or BytesIO  (assumed True)
            header is of type Container                 (assumed True)
            file_info is of type Container              (assumed True)
        '''
        try:
            stream.seek(file_info.SectionDOffset)
            if header.Version == 'XP':
                PrefetchVolumeInformation = pfstructs.PrefetchVolumeInformation17
            elif header.Version == 'SEVEN':
                PrefetchVolumeInformation = pfstructs.PrefetchVolumeInformation23
            elif header.Version == 'EIGHT':
                PrefetchVolumeInformation = pfstructs.PrefetchVolumeInformation26
            else:
                PrefetchVolumeInformation = pfstructs.PrefetchVolumeInformation30
            volumes_info = list()
            for i in range(file_info.SectionDEntriesCount):
                volumes_info_entry = PrefetchVolumeInformation.parse_stream(stream)
                volumes_info_position = stream.tell()
                volumes_info_entry.VolumeCreateTime = WindowsTime(volumes_info_entry.RawVolumeCreateTime).parse()
                stream.seek(file_info.SectionDOffset + volumes_info_entry.VolumeDevicePathOffset)
                volumes_info_entry.VolumeDevicePath = pfstructs.String(\
                        volumes_info_entry.VolumeDevicePathLength, \
                        encoding='utf8').parse(\
                            stream.read(volumes_info_entry.VolumeDevicePathLength*2).replace(b'\x00', b'')\
                        )
                volumes_info.append(volumes_info_entry)
                stream.seek(volumes_info_position)
            return self._clean_transform(volumes_info)
        finally:
            stream.seek(original_position)
    def _parse_filename_strings(self, original_position, stream=None, header=None, file_info=None, file_metrics=None):
        '''
        Args:
            original_position: Integer      => position in stream before parsing this structure
            stream: TextIOWrapper|BytesIO   => stream to read from
            header: Container               => prefetch file header information parsed from stream
            file_info: Container            => file information parsed from stream
            file_metrics: Container         => file metrics array parsed from stream
        Returns:
            List<String>
            List of filename strings associated with file_metrics array
        Preconditions:
            original_position is of type Integer        (assumed True)
            stream is of type TextIOWrapper or BytesIO  (assumed True)
            header is of type Container                 (assumed True)
            file_info is of type Container              (assumed True)
            file_metrics is of type Container           (assumed True)
        '''
        try:
            stream.seek(file_info.SectionCOffset)
            filename_strings = list()
            for file_metric in file_metrics:
                if (stream.tell() - file_info.SectionCOffset) <= file_info.SectionCLength:
                    filename_strings.append(\
                        pfstructs.PrefetchFileNameString.parse_stream(stream)\
                    )
                else:
                    filename_strings.append(None)
            return self._clean_transform(filename_strings)
        finally:
            stream.seek(original_position)
    def _parse_trace_chains(self, original_position, stream=None, header=None, file_info=None):
        '''
        Args:
            original_position: Integer      => position in stream before parsing this structure
            stream: TextIOWrapper|BytesIO   => stream to read from
            header: Container               => prefetch file header information parsed from stream
            file_info: Container            => file information parsed from stream
        Returns:
            List<Container<String, Any>>
            Prefetch file trace chains information array (see: src.structures.prefetch.PrefetchTraceChainEntry)
        Preconditions:
            original_position is of type Integer        (assumed True)
            stream is of type TextIOWrapper or BytesIO  (assumed True)
            header is of type Container                 (assumed True)
            file_info is of type Container              (assumed True)
        '''
        try:
            stream.seek(file_info.SectionBOffset)
            trace_chains = list()
            for i in range(file_info.SectionBEntriesCount):
                trace_chains.append(pfstructs.PrefetchTraceChainEntry.parse_stream(stream))
            return self._clean_transform(trace_chains)
        finally:
            stream.seek(original_position)
    def _parse_file_metrics(self, original_position, stream=None, header=None, file_info=None):
        '''
        Args:
            original_position: Integer      => position in stream before parsing this structure
            stream: TextIOWrapper|BytesIO   => stream to read from
            header: Container               => prefetch file header information parsed from stream
            file_info: Container            => file information parsed from stream
        Returns:
            List<Container<String, Any>>
            Prefetch file metrics information array (see: src.structures.prefetch.PrefetchFileMetrics*)
        Preconditions:
            original_position is of type Integer        (assumed True)
            stream is of type TextIOWrapper or BytesIO  (assumed True)
            header is of type Container                 (assumed True)
            file_info is of type Container              (assumed True)
        '''
        try:
            stream.seek(file_info.SectionAOffset)
            if header.Version == 'XP':
                PrefetchFileMetricsEntry = pfstructs.PrefetchFileMetricsEntry17
            elif header.Version == 'SEVEN':
                PrefetchFileMetricsEntry = pfstructs.PrefetchFileMetricsEntry23
            elif header.Version == 'EIGHT':
                PrefetchFileMetricsEntry = pfstructs.PrefetchFileMetricsEntry26
            else:
                PrefetchFileMetricsEntry = pfstructs.PrefetchFileMetricsEntry30
            file_metrics = list()
            for i in range(file_info.SectionAEntriesCount):
                file_metrics_entry = self._clean_transform(PrefetchFileMetricsEntry.parse_stream(stream))
                if hasattr(file_metrics_entry, 'FileReference'):
                    file_metrics_entry.FileReference = self._clean_transform(file_metrics_entry.FileReference)
                file_metrics.append(file_metrics_entry)
            return self._clean_transform(file_metrics)
        finally:
            stream.seek(original_position)
    def _parse_file_info(self, original_position, stream=None, header=None):
        '''
        Args:
            original_position: Integer      => position in stream before parsing this structure
            stream: TextIOWrapper|BytesIO   => stream to read from
            header: Container               => prefetch file header information parsed from stream
        Returns:
            Container<String, Any>
            Prefetch file information (see src.structures.prefetch.PrefetchFileInformation*)
        Preconditions:
            original_position is of type Integer        (assumed True)
            stream is of type TextIOWrapper or BytesIO  (assumed True)
            header is of type Container                 (assumed True)
        '''
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
        return self._clean_transform(file_info)
    def _parse_header(self, original_position, stream=None):
        '''
        Args:
            original_position: Integer      => position in stream before parsing this structure
            stream: TextIOWrapper|BytesIO   => stream to read from
        Returns:
            Container<String, Any>
            Prefetch file header information (see src.structures.prefetch.PrefetchHeader)
        Preconditions:
            original_position is of type Integer        (assumed True)
            stream is of type TextIOWrapper or BytesIO  (assumed True)
        '''
        header = pfstructs.PrefetchHeader.parse_stream(stream)
        header.Signature = header.RawSignature.decode('utf8')
        header.ExecutableName = header.RawExecutableName.split('\x00')[0]
        header.PrefetchHash = hex(header.RawPrefetchHash).replace('0x', '').upper()
        return self._clean_transform(header)
    def _hash_file(self, algorithm):
        '''
        Args:
            algorithm: String   => hash algorithm to use
        Returns:
            String
            Hex digest of hash of prefetch file
        Preconditions:
            algorithm is of type String
        '''
        try:
            hash = getattr(hashlib, algorithm)()
        except Exception as e:
            raise
            Logger.error('Unable to obtain %s hash of prefetch file (%s)'%(algorithm, str(e)))
            return None
        else:
            with open(self._filepath, 'rb') as pf:
                buffer = pf.read(1024)
                while len(buffer) > 0:
                    hash.update(buffer)
                    buffer = pf.read(1024)
            return hash.hexdigest()
    def get_metadata(self, simple_hash=True):
        '''
        Args:
            simple_hash: Boolean    => whether to only collect SHA256 hash or 
                                       MD5 and SHA1 as well
        Returns:
            Container<String, Any>
            Container of metadata about this prefetch file:
                file_name: prefetch file name
                file_path: full path on local system
                file_size: size of file on local system
                md5hash: MD5 hash of prefetch file
                sha1hash: SHA1 hash of prefetch file
                sha2hash: SHA256 hash of prefetch file
                modify_time: last modification time of prefetch file on local system
                access_time: last access time of prefetch file on local system
                create_time: create time of prefetch file on local system
        Preconditions:
            simple_hash is of type Boolean
        '''
        assert isinstance(simple_hash, bool), 'Simple_hash is of type Boolean'
        return Container(\
            file_name=path.basename(self._filepath),
            file_path=path.abspath(self._filepath),
            file_size=path.getsize(self._filepath),
            md5hash=self._hash_file('md5') if not simple_hash else None,
            sha1hash=self._hash_file('sha1') if not simple_hash else None,
            sha2hash=self._hash_file('sha256'),
            modify_time=datetime.fromtimestamp(path.getmtime(self._filepath), tzlocal()).astimezone(tzutc()),
            access_time=datetime.fromtimestamp(path.getatime(self._filepath), tzlocal()).astimezone(tzutc()),
            create_time=datetime.fromtimestamp(path.getctime(self._filepath), tzlocal()).astimezone(tzutc())\
        )
    def get_stream(self, persist=False):
        '''
        Args:
            persist: Boolean    => whether to persist stream as attribute on self
        Returns:
            TextIOWrapper|BytesIO
            Stream of prefetch file at self._filepath
        Preconditions:
            persist is of type Boolean  (assumed True)
        '''
        stream = open(self._filepath, 'rb') \
            if self._get_version() is not None \
            else BytesIO(DecompressWin10().decompress(self._filepath))
        if persist:
            self._stream = stream
        return stream
    def serialize(self):
        '''
        Args:
            N/A
        Returns:
            Container<String, Any>
            Serializable representation of self in Container object
        Preconditions:
            N/A
        '''
        return self._clean_transform(Container(**self), serialize=True)
    def parse_structure(self, structure, *args, stream=None, **kwargs):
        '''
        '''
        if stream is None:
            stream = self._stream
        structure_parser = getattr(self, '_parse_' + structure, None)
        if structure_parser is None:
            Logger.error('Structure %s is not a known structure'%structure)
            return None
        try:
            prepared_kwargs = self._prepare_kwargs(structure_parser, **kwargs)
        except Exception as e:
            Logger.error('Failed to parse provided kwargs for structure %s (%s)'%(structure, str(e)))
            return None
        original_position = stream.tell()
        try:
            return structure_parser(original_position, *args, stream=stream, **prepared_kwargs)
        except Exception as e:
            Logger.error('Failed to parse %s structure (%s)'%(structure, str(e)))
            return None
    def parse(self):
        '''
        Args:
            N/A
        Procedure:
            Attempt to parse the supplied prefetch file, extracting
            header, file information, file metrics, trace chains,
            filename strings, and volumes information
        Preconditions:
            self._filepath points to valid prefetch file
        '''
        self._stream = self.get_stream()
        try:
            self.header = self.parse_structure('header')
            self.file_info = self.parse_structure('file_info')
            self.file_metrics = self.parse_structure('file_metrics')
            self.filename_strings = self.parse_structure('filename_strings')
            self.trace_chains = self.parse_structure('trace_chains')
            self.volumes_info = self.parse_structure('volumes_info')
            self.file_references = self.parse_structure('file_references')
            self.directory_strings = self.parse_structure('directory_strings')
            return self
        finally:
            try:
                self._stream.close()
            except:
                pass
