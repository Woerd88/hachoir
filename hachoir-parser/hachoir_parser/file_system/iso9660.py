"""
ISO 9660 (cdrom) file system parser.

Documents:
- Standard ECMA-119 (december 1987)
  http://www.nondot.org/sabre/os/files/FileSystems/iso9660.pdf

Author: Victor Stinner
Creation: 11 july 2006
"""

from hachoir_parser import Parser
from hachoir_core.field import (FieldSet, ParserError,
    UInt8, UInt16, UInt16BE, UInt32, UInt32BE, Enum,
    NullBytes, RawBytes, String)
from hachoir_core.endian import LITTLE_ENDIAN, BIG_ENDIAN

class PrimaryVolumeDescriptor(FieldSet):
    endian = LITTLE_ENDIAN
    static_size = 2041*8
    def createFields(self):
        yield NullBytes(self, "unused[]", 1)
        yield String(self, "system_id", 32, "System identifier", strip=" ")
        yield String(self, "volume_id", 32, "Volume identifier", strip=" ")
        yield NullBytes(self, "unused[]", 8)

        # doc below, iso9660 uses both endian

        yield UInt32(self, "space_size_l", "Volume space size Type L")
        yield UInt32BE(self, "space_size_m", "Volume space size Type M")
        yield NullBytes(self, "unused[]", 32)
        yield UInt16(self, "set_size_l", "Volume set size Type L")
        yield UInt16BE(self, "set_size_m", "Volume set size Type M")
        yield UInt16(self, "seq_num_l", "Volume Sequence number Type L")
        yield UInt16BE(self, "seq_num_m", "Volume Sequence number Type L")
        yield UInt16(self, "block_size_l", "Block size Type L")
        yield UInt16BE(self, "block_size_m", "Block size Type M")

        # Temp documentation: https://casper.berkeley.edu/svn/trunk/roach/sw/uboot/disk/part_iso.h

        yield UInt32(self, "path_table_size_l", "Path table size Type L")
        yield UInt32BE(self, "path_table_size_m", "Path table size Type M")
        yield UInt32(self, "occu_lpath", "Location of Occurrence of Type L Path Table")
        yield UInt32(self, "opt_lpath", "Location of Optional of Type L Path Table")
        yield UInt32BE(self, "occu_mpath", "Location of Occurrence of Type M Path Table")
        yield UInt32BE(self, "opt_mpath", "Location of Optional of Type M Path Table")
        #yield RawBytes(self, "root", 34, "Directory Record for Root Directory")
        #yield RootDirectory(self, "root_directory")
        yield DirectoryRecord(self, "root_directory")
        yield String(self, "vol_set_id", 128, "Volume set identifier", strip=" ")
        yield String(self, "publisher", 128, "Publisher identifier", strip=" ")
        yield String(self, "data_preparer", 128, "Data preparer identifier", strip=" ")
        yield String(self, "application", 128, "Application identifier", strip=" ")
        yield String(self, "copyright", 37, "Copyright file identifier", strip=" ")
        yield String(self, "abstract", 37, "Abstract file identifier", strip=" ")
        yield String(self, "biographic", 37, "Biographic file identifier", strip=" ")
        yield String(self, "creation_ts", 17, "Creation date and time", strip=" ")
        yield String(self, "modification_ts", 17, "Modification date and time", strip=" ")
        yield String(self, "expiration_ts", 17, "Expiration date and time", strip=" ")
        yield String(self, "effective_ts", 17, "Effective date and time", strip=" ")
        yield UInt8(self, "struct_ver", "Structure version")
        yield NullBytes(self, "unused[]", 1)
        yield String(self, "app_use", 512, "Application use", strip=" \0")
        yield NullBytes(self, "unused[]", 653)

class BootRecord(FieldSet):
    static_size = 2041*8
    def createFields(self):
        yield String(self, "sys_id", 31, "Boot system identifier", strip="\0")
        yield String(self, "boot_id", 31, "Boot identifier", strip="\0")
        yield RawBytes(self, "system_use", 1979, "Boot system use")

class Terminator(FieldSet):
    static_size = 2041*8
    def createFields(self):
        yield NullBytes(self, "null", 2041)

class Volume(FieldSet):
    endian = BIG_ENDIAN
    TERMINATOR = 255
    type_name = {
        0: "Boot Record",
        1: "Primary Volume Descriptor",
        2: "Supplementary Volume Descriptor",
        3: "Volume Partition Descriptor",
        TERMINATOR: "Volume Descriptor Set Terminator",
    }
    static_size = 2048 * 8
    content_handler = {
        0: BootRecord,
        1: PrimaryVolumeDescriptor,
        TERMINATOR: Terminator,
    }

    def createFields(self):

        yield Enum(UInt8(self, "type", "Volume descriptor type"), self.type_name)
        yield RawBytes(self, "signature", 5, "ISO 9960 signature (CD001)")
        if self["signature"].value != "CD001":
            raise ParserError("Invalid ISO 9960 volume signature")
        yield UInt8(self, "version", "Volume descriptor version")
        cls = self.content_handler.get(self["type"].value, None)
        if cls:
            yield cls(self, "content")
        else:
            yield RawBytes(self, "raw_content", 2048-7)


class DirectoryRecord(FieldSet):
    endian = LITTLE_ENDIAN
    file_flags = {
        0: "Normal File",
        1: "Hidden File",
        2: "Directory",
    }

    def createFields(self):

        #read the lenght of the directory and make it integer
        file_total_length = self.stream.readBytes(self.absolute_address, 1)
        file_total_length = ord(file_total_length)

        if (file_total_length >= 32):
            yield UInt8(self, "length", "Length of Directory Identifier")
            yield UInt8(self, "attr_length", "Extended Attribute Record Length")
            yield UInt32(self, "extent_lpath", "Location of extent (LBA) Type L")
            yield UInt32BE(self, "extent_mpath", "Location of extent (LBA) Type M")
            yield UInt32(self, "extent_size_l", "Size of extent (LBA) Type L")
            yield UInt32BE(self, "extent_size_m", "Size of extent (LBA) Type M")
            yield RawBytes(self, "recording_datetime", 7, "Recording date and time")
            yield Enum(UInt8(self, "file_flag", "File flags"), self.file_flags)
            yield UInt8(self, "file_unit_size", "File unit size for files recorded in interleaved mode, zero otherwise")
            yield UInt8(self, "interleave_gap_size", "Interleave gap size for files recorded in interleaved mode, zero otherwise")
            yield UInt16(self, "volume_seq_number_l", "Volume sequence number, the volume that this extent is recorded on Type L")
            yield UInt16BE(self, "volume_seq_number_m", "Volume sequence number, the volume that this extent is recorded on Type M")
            yield UInt8(self, "file_identifier_length", "Length of file identifier (file name)")
            file_identifier_length = self["file_identifier_length"].value
            yield RawBytes(self, "file_identifier", file_identifier_length, "file name")

            #check if the padding byte is there
            if file_identifier_length % 2 == 0:
                yield UInt8(self, "padding_byte", "Padding byte: if file_identifier_length is even this is set to 0")
                file_padding_byte = 1
            else:
                file_padding_byte = 0

            #check if there are any unused bytes
            if file_total_length - 33 - file_identifier_length - file_padding_byte > 0:
                yield RawBytes(self, "unused[]", file_total_length - 33 - file_identifier_length - file_padding_byte, "unspecified field for system use; must contain an even number of bytes")

class PathTable(FieldSet):
    endian = LITTLE_ENDIAN
    def createFields(self):
        #Are we filling up the Little Endian or Big Endian PathTable?
        islsb = self.name.startswith("path_l")
        UInt16_ = UInt16 if islsb else UInt16BE
        UInt32_ = UInt32 if islsb else UInt32BE
        yield UInt8(self, "length", "Length of Directory Identifier")
        yield UInt8(self, "attr_length", "Extended Attribute Record Length")
        yield UInt32_(self, "location", "Location of Extent where the directory is recorded (LBA)")
        yield UInt16_(self, "parent_dir", "Parent Directory Number in the path table")
        yield String(self, "name", self["length"].value, "Directory Identifier (name)", strip=" ")
        if self["length"].value % 2:
            yield NullBytes(self, "unused[]", 1)

class ISO9660(Parser):
    endian = LITTLE_ENDIAN
    MAGIC = "\x01CD001"
    NULL_BYTES = 0x8000
    PARSER_TAGS = {
        "id": "iso9660",
        "category": "file_system",
        "description": "ISO 9660 file system",
        "min_size": (NULL_BYTES + 6)*8,
        "magic": ((MAGIC, NULL_BYTES*8),),
    }

    def validate(self):

        #first 16 sectors are system area, after that the "\x01CD001" should be there

        #first check if its a iso with sector size 2048 (0x800)
        #(ISO9660/DVD/2048) (ISO DISC IMAGE, only sectors data)
        if self.stream.readBytes(16 * 2048 * 8, len(self.MAGIC)) == self.MAGIC:
            return True

        #Second check if its a iso with sector size 2352 (0x930) + sector header of 16 bytes
        #ISO9660/MODE1/2352 (CD SECTORS)
        if self.stream.readBytes( ((16 * 2352) + 16) * 8, len(self.MAGIC)) == self.MAGIC:
            return True

        #Third check if its a iso with sector size 2352 (0x930) + sector header of 24 bytes
        #ISO9660/MODE2/FORM1/2352 (CD SECTORS)
        if self.stream.readBytes( ((16 * 2352) + 24) * 8, len(self.MAGIC)) == self.MAGIC:
            return True

        return "Invalid signature"

    def createFields(self):

        #Step 1: Skip this system area
        #The first 16 sectors are system area, but we don't know what sector size is being used
        # let's check sector size 2046 (16 sectors x 2046 bytes per sector = 0x8000)
        if self.stream.readBytes(16 * 2048 * 8, len(self.MAGIC)) == self.MAGIC:
            #(ISO9660/DVD/2048) (ISO DISC IMAGE, only sectors data)
            iso_mode = 0
            sector_size = 2048
            sector_header_size = 0

        # let's check sector size 2532 (16 sectors x 2532 bytes per sector = 0x9300)
        # and add the sectorheader of 16 bytes
        elif self.stream.readBytes( ((16 * 2352) + 16) * 8, len(self.MAGIC)) == self.MAGIC:
            #ISO9660/MODE1/2352 (CD SECTORS)
            iso_mode = 1
            sector_size = 2352
            sector_header_size = 16

        # let's check sector size 2532 (16 sectors x 2532 bytes per sector = 0x9300)
        # and add the sectorheader of 24 bytes
        elif self.stream.readBytes( ((16 * 2352) + 24) * 8, len(self.MAGIC)) == self.MAGIC:
            #ISO9660/MODE2/FORM1/2352 (CD SECTORS)
            iso_mode = 2
            form = 1
            sector_size = 2352
            sector_header_size = 24

        #okay now we have the sector size skip the system area
        yield self.seekByte( (16 * sector_size), null=True)

        pathtable_l_offset = 0
        pathtable_l_size = 0

        pathtable_m_offset = 0
        pathtable_m_size = 0

        directory_offset = 0
        directory_size = 0

        #Step2: list all volumes untill the terminator shows up
        while True:

            #ISO Mode 1 and 2 has a sector header
            if iso_mode == 1:
                yield RawBytes(self, "sector_header", 16, "CD-ROM XA Mode 1 header")
            elif iso_mode == 2:
                yield RawBytes(self, "sector_header", 24, "CD-ROM XA Mode 2 header")

            #2048 Bytes user data
            volume = Volume(self, "volume[]")
            yield volume

            #Check if we have a sector ending
            if iso_mode == 1:
                yield RawBytes(self, "sector_end", 4 + 8 + 276, "CD-ROM XA Mode 1 ending")
            if iso_mode == 2:
                yield RawBytes(self, "sector_end", 4 + 276, "CD-ROM XA Mode 2 ending")

            if volume["type"].value == 1: # PrimaryVolumeDescriptor

                #Step2.1 Extract Location of path table
                # Multiply LBA by sector size to get index offset
                pathtable_l_offset = volume["content/occu_lpath"].value * sector_size
                pathtable_l_size = volume["content/path_table_size_l"].value
                pathtable_m_offset = volume["content/occu_mpath"].value * sector_size
                pathtable_m_size = volume["content/path_table_size_m"].value

                #Step2.2 Extract Location of next directory record from root directory
                # Multiply LBA by sector size to get index offset
                directory_offset = volume["content/root_directory/extent_lpath"].value * sector_size
                directory_size = volume["content/root_directory/extent_size_l"].value
                # Fall back to MSB path table if necessary
                if not directory_offset and volume["content/root_directory/extent_mpath"].value:
                    directory_offset = volume["content/root_directory/extent_mpath"].value * sector_size
                    directory_size = volume["content/root_directory/extent_size_m"].value

            elif volume["type"].value == Volume.TERMINATOR:
                break

        #Step3.1: Jump to the pathtable location (little Endian) thas was extracted from the PrimaryVolumeDescriptor
        #       And list all path table entries
        if pathtable_l_offset:

            #Most of the time this table is located right after the volumes
            #in this case don't add it as a field, because it will be null, and this caused the framework to end this parser
            if (pathtable_l_offset * 8) > self.current_size:
                yield self.seekByte(pathtable_l_offset, relative=False, null=True)

            #ISO Mode 1 and 2 has a sector header
            if iso_mode == 1:
                yield RawBytes(self, "sector_header", 16, "CD-ROM XA Mode 1 header")
            elif iso_mode == 2:
                yield RawBytes(self, "sector_header", 24, "CD-ROM XA Mode 2 header")

            while True:
                pathtable = PathTable(self, "path_l[]")
                yield pathtable
                #divide address and size by 8 since its stored in amount of bits
                currentpath = (pathtable.absolute_address >> 3) + (pathtable.size >> 3)
                if currentpath >= pathtable_l_offset + pathtable_l_size + sector_header_size:
                    break

            #seek to the end of the sextor so we can mark the sector ending properly
            yield self.seekByte(pathtable_l_offset + sector_header_size + 2048, relative=False, null=True)

            #Check if we have a sector ending
            if iso_mode == 1:
                yield RawBytes(self, "sector_end", 4 + 8 + 276, "CD-ROM XA Mode 1 ending")
            if iso_mode == 2:
                yield RawBytes(self, "sector_end", 4 + 276, "CD-ROM XA Mode 2 ending")

        #Step3.2: Jump to the pathtable location (Big Endian) thas was extracted from the PrimaryVolumeDescriptor
        #       And list all path table entries
        if pathtable_m_offset:

            #Most of the time this table is located right after the volumes
            #in this case don't add it as a field, because it will be null, and this caused the framework to end this parser
            if (pathtable_m_offset * 8) > self.current_size:
                yield self.seekByte(pathtable_m_offset, relative=False, null=True)

            #ISO Mode 1 and 2 has a sector header
            if iso_mode == 1:
                yield RawBytes(self, "sector_header", 16, "CD-ROM XA Mode 1 header")
            elif iso_mode == 2:
                yield RawBytes(self, "sector_header", 24, "CD-ROM XA Mode 2 header")

            while True:
                pathtable = PathTable(self, "path_m[]")
                yield pathtable
                #divide address and size by 8 since its stored in amount of bits
                currentpath = (pathtable.absolute_address >> 3) + (pathtable.size >> 3)
                if currentpath >= pathtable_m_offset + pathtable_m_size + sector_header_size:
                    break

            #seek to the end of the sextor so we can mark the sector ending properly
            yield self.seekByte(pathtable_m_offset + sector_header_size + 2048, relative=False, null=True)

            #Check if we have a sector ending
            if iso_mode == 1:
                yield RawBytes(self, "sector_end", 4 + 8 + 276, "CD-ROM XA Mode 1 ending")
            if iso_mode == 2:
                yield RawBytes(self, "sector_end", 4 + 276, "CD-ROM XA Mode 2 ending")

        #directory_offset = 0

        #Step4: Jump to the directions location thas was extracted from the PrimaryVolumeDescriptor
        if directory_offset:

            if directory_offset * 8 > self.current_size:
                yield self.seekByte(directory_offset, relative=False)

            #Loop over sectors
            while True:

                #ISO Mode 1 and 2 has a sector header
                if iso_mode == 1:
                   yield RawBytes(self, "sector_header", 16, "CD-ROM XA Mode 1 header")
                elif iso_mode == 2:
                   yield RawBytes(self, "sector_header", 24, "CD-ROM XA Mode 2 header")

                #Loop over the directory records
                while True:

                    #check if there is a directory record
                    directory_record_length = self.stream.readBytes(self.current_size, 1)
                    directory_record_length = ord(directory_record_length)

                    if directory_record_length > 0:
                        directory = DirectoryRecord(self, "directory_records[]")
                        yield directory
                    else:
                        break;

                #skoop over to the end of the sector
                directory_offset = directory_offset + sector_header_size + directory_size
                yield self.seekByte(directory_offset, relative=False)

                #Check if we have a sector ending
                if iso_mode == 1:
                    yield RawBytes(self, "sector_end", 4 + 8 + 276, "CD-ROM XA Mode 1 ending")
                if iso_mode == 2:
                    yield RawBytes(self, "sector_end", 4 + 276, "CD-ROM XA Mode 2 ending")

                #update the directory_offset so it will always point to the start of sector
                #is needed when there are sector ends
                directory_offset = self.current_size / 8

        #Last Step: Did we leave anything unparsed? ... well mark it as end
        if self.current_size < self._size:
            yield self.seekBit(self._size, "end")
