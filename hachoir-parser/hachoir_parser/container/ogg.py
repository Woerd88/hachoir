#
# Ogg parser
# Author Julien Muchembled <jm AT jm10.no-ip.com>
# Created: 10 june 2006
#

from hachoir_parser import Parser
from hachoir_core.field import (Field, FieldSet,
    NullBits, Bit, Bits, Enum,
    UInt8, UInt16, UInt24, UInt32, UInt64,
    RawBytes, String, PascalString32)
from hachoir_core.endian import LITTLE_ENDIAN, BIG_ENDIAN

class XiphInt(Field):
    """
    Positive integer with variable size. Values bigger than 254 are stored as
    (255, 255, ..., rest): value is the sum of all bytes.

    Example: 1000 is stored as (255, 255, 255, 235), total = 255*3+235 = 1000
    """
    def __init__(self, parent, name, max_size=None, description=None):
        Field.__init__(self, parent, name, size=0, description=description)
        value = 0
        addr = self.absolute_address
        while max_size is None or self._size < max_size:
            byte = parent.stream.readBits(addr, 8, LITTLE_ENDIAN)
            value += byte
            self._size += 8
            if byte != 0xff:
                break
            addr += 8
        self.createValue = lambda: value

class Lacing(FieldSet):
    def createFields(self):
        size = self.size
        while size:
            field = XiphInt(self, 'size[]', size)
            yield field
            size -= field.size

def parseMetadata(parent):
    yield PascalString32(parent, 'vendor', charset="UTF-8")
    yield UInt32(parent, 'count')
    for index in xrange(parent["count"].value):
        yield PascalString32(parent, 'metadata[]', charset="UTF-8")
    if parent.current_size != parent.size:
        yield UInt8(parent, "framing_flag")

PIXEL_FORMATS = {
    0: "4:2:0",
    2: "4:2:2",
    3: "4:4:4",
}

def parseTheoraHeader(parent):
    yield UInt8(parent, "version_major")
    yield UInt8(parent, "version_minor")
    yield UInt8(parent, "version_revision")
    yield UInt16(parent, "width", "Width*16 in pixel")
    yield UInt16(parent, "height", "Height*16 in pixel")

    yield UInt24(parent, "frame_width")
    yield UInt24(parent, "frame_height")
    yield UInt8(parent, "offset_x")
    yield UInt8(parent, "offset_y")

    yield UInt32(parent, "fps_num", "Frame per second numerator")
    yield UInt32(parent, "fps_den", "Frame per second denominator")
    yield UInt24(parent, "aspect_ratio_num", "Aspect ratio numerator")
    yield UInt24(parent, "aspect_ratio_den", "Aspect ratio denominator")

    yield UInt8(parent, "color_space")
    yield UInt24(parent, "target_bitrate")
    yield Bits(parent, "quality", 6)
    yield Bits(parent, "gp_shift", 5)
    yield Enum(Bits(parent, "pixel_format", 2), PIXEL_FORMATS)
    yield Bits(parent, "spare_config", 3)

def parseVorbisHeader(parent):
    yield UInt32(parent, "vorbis_version")
    yield UInt8(parent, "audio_channels")
    yield UInt32(parent, "audio_sample_rate")
    yield UInt32(parent, "bitrate_maximum")
    yield UInt32(parent, "bitrate_nominal")
    yield UInt32(parent, "bitrate_minimum")
    yield Bits(parent, "blocksize_0", 4)
    yield Bits(parent, "blocksize_1", 4)
    yield UInt8(parent, "framing_flag")

class Chunk(FieldSet):
    tag_info = {
        "vorbis": {
            3: ("comment", parseMetadata),
            1: ("vorbis_hdr", parseVorbisHeader),
        }, "theora": {
            128: ("theora_hdr", parseTheoraHeader),
            129: ("comment", parseMetadata),
        }
    }
    def __init__(self, *args, **kw):
        FieldSet.__init__(self, *args, **kw)
        if 7*8 <= self.size:
            try:
                self._name, self.parser = self.tag_info[self["codec"].value][self["type"].value]
                if self._name == "theora_hdr":
                    self.endian = BIG_ENDIAN
            except KeyError:
                self.parser = None
        else:
            self.parser = None

    def createFields(self):
        if 7*8 <= self.size:
            yield UInt8(self, 'type')
            yield String(self, 'codec', 6)
        if self.parser:
            for field in self.parser(self):
                yield field
        else:
            size = (self.size - self.current_size) // 8
            if size:
                yield RawBytes(self, "raw", size)

class OggPage(FieldSet):
    def __init__(self, *args):
        FieldSet.__init__(self, *args)
        size = 27
        self.lacing_size = self['lacing_size'].value
        if self.lacing_size:
            size += self.lacing_size
            lacing = self['lacing']
            self.packet_size = [ field.value for field in lacing ]
            size += sum(self.packet_size)
        self._size = size * 8

    def createFields(self):
        yield String(self, 'capture_pattern', 4, charset="ASCII")
        if self['capture_pattern'].value != 'OggS':
            self.warning('Invalid signature. An Ogg page must start with "OggS".')
        yield UInt8(self, 'stream_structure_version')
        yield Bit(self, 'continued_packet')
        yield Bit(self, 'first_page')
        yield Bit(self, 'last_page')
        yield NullBits(self, 'unused', 5)
        yield UInt64(self, 'abs_granule_pos')
        yield UInt32(self, 'serial')
        yield UInt32(self, 'page')
        yield UInt32(self, 'checksum')
        yield UInt8(self, 'lacing_size')
        if self.lacing_size:
            yield Lacing(self, "lacing", size=self.lacing_size*8)
            for packet_size in self.array("lacing/size"):
                if packet_size.value:
                    yield Chunk(self, "chunk[]", size=packet_size.value*8)

class OggFile(Parser):
    MAGIC = "OggS"
    tags = {
        "id": "ogg",
        "category": "container",
        "file_ext": ("ogg", "ogm"),
        "mime": (
            "application/ogg", "application/x-ogg",
            "audio/ogg", "audio/x-ogg",
            "video/ogg", "video/x-ogg",
            "video/theora", "video/x-theora",
         ),
#        "magic": ((MAGIC, 0),),
        "min_size": 28*8,
        "description": "Ogg multimedia container"
    }
    endian = LITTLE_ENDIAN

    def validate(self):
        if self.stream.readBytes(0, 4) != self.MAGIC:
            return "Wrong signature"
        else:
            return True

    def createMimeType(self):
        if "theora_hdr" in self["page[0]"]:
            return "video/theora"
        elif "vorbis_hdr" in self["page[0]"]:
            return "audio/vorbis"
        else:
            return "application/ogg"

    def createDescription(self):
        if "theora_hdr" in self["page[0]"]:
            return u"Ogg/Theora video"
        elif "vorbis_hdr" in self["page[0]"]:
            return u"Ogg/Vorbis audio"
        else:
            return u"Ogg multimedia container"


    def createFields(self):
        while not self.eof:
            yield OggPage(self, "page[]")
