#!/usr/bin/python2
from argparse import ArgumentParser
from struct import pack, unpack
from binascii import unhexlify, hexlify

import re

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
    def bytes_to_long(self, data):
        return unpack('!I', data)[0]


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
    def segments(self):
        return [self.size, self.type, self.data + self.crc]

    @property
    def raw(self):
        return ''.join(self.chunkss)


class Info(Helper):
    def __init__(self, pathname):
        with open(pathname, 'rb') as f:
            self.content = f.read()

        self.chunks = []
        self.pos = 8

        assert self.content[:8] == HEADER, \
        'File must be a PNG Image'

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

    def lookup(self):
        data = str(self.content[8:])
        types = self.locate_chunk(data)    
        pairs = [(types[i], types[i+1]) for i in range(len(types)-1)]

        for pair in pairs: 
            previ, nexti = pair
            
            rule = re.compile('(.{4}%s.*?)%s' % (previ, nexti), re.S)
            offset = self.parse_chunk(data, rule)
            data = data[offset: ]

        self.parse_chunk(data)

    def display(self):
        columns = ['No', 'Type', 'Offset', 'Size', 'Data Length', 'CRC', ]
        template = '{0:<3}{1:<5}{2:<10}{3:<10}{4:<12}{5:<2}' 

        print(template.format(*columns))
        for n, i in enumerate(self.chunks):
            _size = self.bytes_to_long(i.size)
            _type = i.type
            _crc  = hexlify(i.crc)
            _data = len(i.data)
            _pos  = hex(i.offset)
            
            print template.format(n, _type, _pos, _size, _data, _crc)

    def raw(self):
        return HEADER + ''.join(i.raw for i in self.chunks)


if __name__ == "__main__":
    parser = ArgumentParser(description='Simple pngchunk info based on list of chunk type')
    parser.add_argument('png_image', metavar='png_image', type=str, help='Path to png image')
    args = parser.parse_args()

    info = Info(args.png_image)
    info.lookup()
    info.display()