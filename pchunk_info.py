#!/usr/bin/python2
from collections import OrderedDict
from argparse import ArgumentParser
from argparse import Namespace
from binascii import unhexlify, hexlify
from enum import Enum

import os
import re
import struct
import zlib

__description__ = 'simple pngchunk info based on list of chunk type'
__author__ = 'hanasuru'
__version__ = '0.1'

HEADER = b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a'
CHUNK_TYPE = [
    'IHDR',
    'tEXt',
    'zTXt',
    'iTXt',
    'tRNS',
    'cHRM',
    'gAMA',
    'iCCP',
    'sRGB',
    'bKGD',
    'pHYs',
    'hIST',
    'sPLT',
    'sBIT',
    'fcTL', # APNG only
    'acTL', # APNG only
    'fdAT', # APNG only
    'tIME',
    'PLTE',
    'oFFs',
    'pCAL',
    'sCAL',
    'sTER',
    'fRAc',
    'IDAT',
    'IEND'
]


class Helper:
    @staticmethod
    def bytes_to_long(data):
        return struct.unpack('!I', data)[0]

    @staticmethod
    def calc_size(obj):
        obj.seek(0, 2)
        return obj.tell()

    @staticmethod
    def calc_crc32(data):
        checksum = zlib.crc32(data) % (1<<32)
        return struct.pack('>I', checksum)

    @staticmethod
    def exclude_arg(namespace, arg=None):
        if arg:
            temp = vars(namespace)
            filtered = {n: temp[n] for n in temp if n!=arg}
            namespace = Namespace(**filtered)
        return namespace        


class ChunkNotFoundError(Exception):
    def __init__(self, message="Unknown Chunk type"):
        super(Exception, self).__init__(self.message)


class ChecksumError(Exception):
    def __init__(self, message="Checksum error"):
        super(Exception, self).__init__(self.message)


class EOFException(Exception):
    def __init__(self, message="End of file"):
        super(Exception, self).__init__(self.message)


class Chunk:
    def __init__(self, data, pos):
        self.size = self.get_size(data)
        self.type = self.get_type(data)
        self.data = self.get_data(data)
        self.crc  = self.get_crc(data)
        self.offset = self.get_offset(pos)

    def get_size(self, data):
        return data[:4]

    def get_type(self, data):
        return data[4:8]

    def get_data(self, data):
        return data[8:-4]

    def get_crc(self, data):
        return data[-4: ]

    def get_offset(self, pos):
        return pos + 4

    @property
    def chunks(self):
        return [self.size, self.type, self.data + self.crc]

    @property
    def raw(self):
        return ''.join(self.chunks)


class TypeBasedParser(object):
    def __init__(self, content):
        self.chunks = []
        self.pos = 8
        self.content = content

    def locate_chunk(self, data):
        rule = r'|'.join('(%s)' % (_) for _ in CHUNK_TYPE)
        match = re.findall(rule, data)

        return [n for m in match for n in m if n]

    def parse_chunk(self, content, rule=None):
        if rule:
            content = rule.search(content).group(1)[:-4]
        self.chunks.append(Chunk(content, self.pos))
        self.pos += len(content)
        return len(content)

    def run(self):
        data  = self.content[self.pos: ]
        types = self.locate_chunk(data)    
        pairs = [(types[i], types[i+1]) for i in range(len(types)-1)]

        for pair in pairs: 
            previ, nexti = pair
            
            rule = re.compile('(.{4}%s.*?)%s' % (previ, nexti), re.S)
            offset = self.parse_chunk(data, rule)
            data = data[offset: ]

        self.parse_chunk(data)


class DefaultParser(Helper):
    def __init__(self, content):
        self.chunks = []
        self.pos = 8
        self.content = content

    def parse_chunk(self, length):
        begin, end = (self.pos, self.pos+length)
        content = self.content[begin: end]
        self.chunks.append(Chunk(content, self.pos))
        self.pos += len(content)

    def run(self):
        while self.pos < len(self.content):
            try:
                begin, end = (self.pos, self.pos+4)
                length = Helper.bytes_to_long(self.content[begin: end])
                self.parse_chunk(length + 12)
            except struct.error:
                break
        
        if self.chunks[-1].type not in CHUNK_TYPE:
            raise ChunkNotFoundError, 'Unknown chunk type'
        elif length > len(self.content):
            raise IndexError, 'Out of range'
 

class Info(Helper):
    def __init__(self, filename, options):
        with open(filename, 'rb') as f:
            self.filename = filename
            self.content = f.read()
            self.filesize = Helper.calc_size(f)
            self.options = options
            self.chunks = dict()

        assert self.content[:8] == HEADER, 'File must be a PNG Image'

    def lookup(self):
        try:
            parser = DefaultParser(self.content)
            parser.run()
        except Exception as e:
            parser = TypeBasedParser(self.content)
            parser.run()
        finally:
            self.chunks = parser.chunks
            self.selection()

    def display(self):
        columns = ['Id', 'Type', 'Offset', 'Size', 'Data Length', 'CRC', ]
        template = '{0:<5}{1:<5}{2:<10}{3:<13}{4:<12}{5:<2}' 

        print 'Filename:', self.filename
        print 'Size:', self.filesize
        
        print '\nChunk Info\n', template.format(*columns)
        for n, c in self.chunks.iteritems():
            _size = Helper.bytes_to_long(c.size)
            _type = c.type
            _crc  = self.check_crc(c.crc, c)
            _data = len(c.data)
            _pos  = hex(c.offset)
            
            print template.format(n, _type, _pos, _size, _data, _crc)
        print

    def check_crc(self, checksum, data):
        data = Helper.calc_crc32(data.type + data.data)
        if checksum != data:
            return '{} (Must be {})'.format(
                hexlify(checksum), hexlify(data)
            )
        return hexlify(checksum)

    def selection(self):
        if self.options.type:
            self.chunks = {
                n:c for n,c in enumerate(self.chunks)
                if c.type in self.options.type
                and n < self.options.limit
            }
        elif self.options.object:
            self.chunks = [
                (n,c) for n,c in enumerate(self.chunks)
                if str(n) in self.options.object 
                and n < self.options.limit 
            ]
            self.chunks = OrderedDict(sorted(self.chunks))
        else:
            self.chunks = {
                n:c for n,c in enumerate(self.chunks)
                if n < self.options.limit
            }

    def extract(self):
        if self.options.extract:
            try:
                os.makedirs('chunks/')
            except OSError:
                pass
            
            template = 'chunks/{}-{}'
            for n, c in self.chunks.iteritems():
                with open(template.format(n, c.type), 'wb') as f:
                    f.write(c.raw)
            
            print 'Extracted {} chunks'.format(len(self.chunks))

    def dump(self):
        if self.options.dump:
            with open(self.options.dump, 'wb') as f:
                f.write(self.raw_data())

            print 'Dump selected chunks into {}'.format(self.options.dump)
        
        if self.options.fix_crc:
            for n, c in self.chunks.iteritems():
                c.crc = Helper.calc_crc32(c.type + c.data)
            
            with open('fixed.png', 'wb') as f:
                f.write(self.raw_data())

            print 'Repaired CRC error & created fixed.png'

    def raw_data(self):
        return HEADER + ''.join(c.raw for c in self.chunks.values())


if __name__ == "__main__":
    parser = ArgumentParser(description='Simple pngchunk info based on list of chunk type')
    parser.add_argument('file', nargs='+', metavar='file', help='a PNG image')
    parser.add_argument('--type', '-t', nargs='+', metavar='chunk_type', help='Filter chunk by type')
    parser.add_argument('--dump', '-d', metavar='output', help='Dump raw chunk by selection')
    parser.add_argument('--extract', '-e', action='store_true', help='Extract chunk by selection')
    parser.add_argument('--object', '-o', nargs='+', metavar='id', help='Filter chunk by object id')
    parser.add_argument('--limit',  metavar='N', type=int, default=9999, help='Number of chunk output')
    parser.add_argument('--fix-crc', action='store_true', help='Fix CRC error and populate new image')
    
    arguments = parser.parse_args()
    options = Helper.exclude_arg(arguments, 'file')
    
    for imgs in arguments.file:
        info = Info(imgs, options)
        info.lookup()

        if (options.extract
            or options.dump
            or options.fix_crc):
            
            info.extract()
            info.dump()
            continue

        info.display()