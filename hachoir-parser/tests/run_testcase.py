#!/usr/bin/env python2.4
# -*- coding: utf-8 -*-
DOWNLOAD_SCRIPT = "download_testcase.py"
"""
Test hachoir-parser using the testcase.
Use script %s to download and check the testcase.
""" % DOWNLOAD_SCRIPT

# Configure Hachoir
from hachoir_core import config
config.use_i18n = False  # Don't use i18n
config.quiet = True      # Don't display warnings

from hachoir_core.field import FieldError
from hachoir_core.i18n import getTerminalCharset
from hachoir_core.tools import humanFilesize
from hachoir_core.error import HachoirError
from hachoir_core.stream import InputStreamError
from hachoir_parser import createParser
from hachoir_core.compatibility import all
from locale import setlocale, LC_ALL
import os
import sys

###########################################################################

def checkValue(parser, path, value):
    sys.stdout.write("  - Check field %s.value=%s (%s): "
        % (path, repr(value), value.__class__.__name__))
    sys.stdout.flush()
    try:
        read = parser[path].value
        if read == value:
            sys.stdout.write("ok\n")
            return True
        else:
            sys.stdout.write("wrong value (%s, %s)\n"
                % (repr(read), read.__class__.__name__))
            return False
    except FieldError, err:
        sys.stdout.write("field error: %s\n" % unicode(err))
        return False

def checkDisplay(parser, path, value):
    sys.stdout.write("  - Check field %s.display=%s (%s): "
        % (path, repr(value), value.__class__.__name__))
    sys.stdout.flush()
    try:
        read = parser[path].display
        if read == value:
            sys.stdout.write("ok\n")
            return True
        else:
            sys.stdout.write("wrong value (%s, %s)\n"
                % (repr(read), read.__class__.__name__))
            return False
    except FieldError, err:
        sys.stdout.write("field error: %s\n" % unicode(err))
        return False

def checkDesc(parser, path, value):
    sys.stdout.write("  - Check field %s.description=%s (%s): "
        % (path, repr(value), value.__class__.__name__))
    sys.stdout.flush()
    try:
        read = parser[path].description
        if read == value:
            sys.stdout.write("ok\n")
            return True
        else:
            sys.stdout.write("wrong value (%s, %s)\n"
                % (repr(read), read.__class__.__name__))
            return False
    except FieldError, err:
        sys.stdout.write("field error: %s\n" % unicode(err))
        return False

def checkNames(parser, path, names):
    sys.stdout.write("  - Check field names %s=(%s) (%u): "
        % (path, ", ".join(names), len(names)))
    sys.stdout.flush()
    try:
        fieldset = parser[path]
        if len(fieldset) != len(names):
            sys.stdout.write("invalid length (%u)\n" % len(fieldset))
            return False
        names = list(names)
        read = list(field.name for field in fieldset)
        if names != read:
            sys.stdout.write("wrong names (%s)\n" % ", ".join(read))
            return True
        else:
            sys.stdout.write("ok\n")
            return True
    except FieldError, err:
        sys.stdout.write("field error: %s\n" % unicode(err))
        return False

###########################################################################

def checkYellowdude(parser): return (
    checkValue(parser, "/main/version/version", 2),
    checkNames(parser, "/main", ("type", "size", "version", "obj_mat")))

def checkLogoUbuntu(parser): return (
    checkValue(parser, "/header/width", 331),
    checkValue(parser, "/time/second", 46))

def checkClick(parser): return (
    checkValue(parser, "/info/producer/text", "Sound Forge 4.5"),
    checkValue(parser, "/format/sample_per_sec", 22050))

def checkMBR(parser): return (
    checkValue(parser, "/mbr/header[1]/size", 65545200),
    checkDisplay(parser, "/mbr/signature", u"0xaa55"))

def checkFlashMob(parser): return (
    checkValue(parser, "/Segment[0]/Cues/CuePoint[1]/CueTrackPositions[0]"
          + "/CueClusterPosition/cluster/BlockGroup[14]/Block/block/timecode", 422),
    checkValue(parser, "/Segment[0]/Tags[0]/Tag[0]/SimpleTag[3]/TagString/unicode",
          u"\xa9 dadaprod, licence Creative Commons by-nc-sa 2.0 fr"))

def check10min(parser): return (
    checkValue(parser, "/Segment[0]/size", None),
    checkValue(parser, "/Segment[0]/Tracks[0]/TrackEntry[0]/CodecID/string", "V_MPEG4/ISO/AVC"))

def checkWormuxICO(parser): return (
    checkValue(parser, "icon_header[0]/height", 16),
    checkValue(parser, "icon_data[0]/header/hdr_size", 40))

def checkCDA(parser): return (
    checkValue(parser, "filesize", 36),
    checkValue(parser, "/cdda/track_no", 4),
    checkDisplay(parser, "/cdda/disc_serial", "0008-5C48"),
    checkValue(parser, "/cdda/rb_length/second", 53))

def checkSheepMP3(parser): return (
    checkValue(parser, "/id3v2/field[6]/content/text",
        u'Stainless Steel Provider is compilated to the car of Twinstar.'),
    checkValue(parser, "/frames/frame[0]/use_padding", False))

def checkAU(parser): return (
    checkValue(parser, "info", "../tmp/temp.snd"),
    checkDisplay(parser, "codec", "8-bit ISDN u-law"))

def checkGzip(parser):
    return (checkValue(parser, "filename", "test.txt"),)

def checkSteganography(parser): return (
    checkValue(parser, "/frames/padding[0]", "misc est un canard\r"),
    checkDesc(parser, "/frames", 'Frames: Variable bit rate (VBR)'),
    checkDesc(parser, "/frames/frame[1]", u'MPEG-1 layer III, 160.0 Kbit/sec, %.1f KHz' % 44.1))

def checkRPM(parser): return (
    checkValue(parser, "name", "ftp-0.17-537"),
    checkValue(parser, "os", 1),
    checkValue(parser, "checksum/content_item[2]/value", 50823),
    checkValue(parser, "header/content_item[15]/value", "ftp://ftp.uk.linux.org/pub/linux/Networking/netkit"))

def checkJPEG(parser): return (
    checkValue(parser, "app0/content/jfif", "JFIF\x00"),
    checkValue(parser, "app0/content/ver_maj", 1),
    checkValue(parser, "photoshop/content/signature", "Photoshop 3.0"),
    checkValue(parser, "photoshop/content/copyright_flg/content", "\0\0"),
    checkValue(parser, "exif/content/header", "Exif\0\0"),
    checkValue(parser, "exif/content/header2", 42))

def checkTAR(parser): return (
    checkDisplay(parser, "file[0]/name", u'"dummy.txt"'),
    checkDisplay(parser, "file[1]/mode", u'"0000755"'),
    checkDisplay(parser, "file[1]/type", u'Directory'),
    checkDisplay(parser, "file[2]/devmajor", u'(empty)'),
)

def checkCornerBMP(parser): return (
    checkValue(parser, "header/width", 189),
    checkValue(parser, "header/used_colors", 70),
    checkDesc(parser, "palette/color[1]", "RGB color: White (opacity: 0%)"),
    checkValue(parser, "pixels/line[26]/pixel[14]", 28),
)

def checkCACertClass3(parser): return (
    checkDisplay(parser, "seq[0]/class", u'universal'),
    checkDesc(parser, "seq[0]/seq[0]/seq[0]/obj_id[0]", "Object identifier: 1.2.840.113549.1.1.4"),
    checkValue(parser, "seq[0]/seq[0]/seq[1]/set[0]/seq[0]/print_str[0]/value", u"Root CA"),
    checkValue(parser, "seq[0]/seq[0]/seq[1]/set[3]/seq[0]/ia5_str[0]/value", u"support@cacert.org"),
    checkValue(parser, "seq[0]/bit_str[0]/size", 513),
)

def checkPYC(parser): return (
    checkValue(parser, "/code/consts/item[0]", 42),
    checkValue(parser, "/code/stack_size", 4),
    checkValue(parser, "/code/consts/item[1]", 2535301200456458802993406410752L),
    checkValue(parser, "/code/consts/item[4]", 0.3j),
    checkValue(parser, "/code/consts/item[8]", "abc"),
    checkValue(parser, "/code/filename", "pyc_example.py"))

def checkReferenceMapClass(parser): return (
    checkValue(parser, "/minor_version", 3),
    checkValue(parser, "/major_version", 45),
    checkValue(parser, "/constant_pool_count", 326),
    checkValue(parser, "/constant_pool/constant_pool[324]/bytes", u"([Ljava/lang/Object;Ljava/lang/Object;)V"),
    checkValue(parser, "/super_class", 80),
    checkValue(parser, "/interfaces_count", 0),
    checkValue(parser, "/fields_count", 16),
    checkValue(parser, "/fields/fields[3]/attributes/attributes[0]/attribute_name_index", 93),
    checkValue(parser, "/methods_count", 31),
    checkValue(parser, "/methods/methods[30]/attributes/attributes[0]/code_length", 5),
    checkValue(parser, "/attributes_count", 3),
    checkValue(parser, "/attributes/attributes[2]/classes/classes[1]/inner_name_index", 83))

def checkClaqueBeignet(parser): return (
    checkDesc(parser, "rect", "Rectangle: 550x400"),
    checkDisplay(parser, "frame_rate", "24.0"),
    checkDesc(parser, "bkgd_color[0]/color", "RGB color: #CC9933"),
    checkDisplay(parser, "def_sound[0]/rate", "11.0 KHz"),
    checkValue(parser, "def_sound[0]/len", 1661),
    checkValue(parser, "sound_hdr2[0]/sound_is_16bit", False),
    checkValue(parser, "export[0]/export[0]/name", u"C bras"),
)

def checkBreakdance(parser): return (
    checkDisplay(parser, "/audio[0]/codec", "MP3"),
    checkValue(parser, "/audio[2]/timestamp", 52),
    checkDisplay(parser, "/video[0]/codec", "Sorensen H.263"),
    checkValue(parser, "/metadata/entry[1]/item[8]/attr[1]/item[4]/value/exponent", 20),
)

def checkArpDnsPingDns(parser): return (
    checkValue(parser, "/packet[5]/ipv4/ttl", 120),
    checkDisplay(parser, "/packet[3]/ts_epoch", "2006-11-23 23:13:19"),
    checkDisplay(parser, "/packet[3]/ipv4/src", "212.27.54.252"),
    checkDisplay(parser, "/packet[7]/udp/src", "DNS"),
)

def checkExt2(parser): return (
    checkDisplay(parser, "/superblock/last_check", u'2006-12-04 22:56:37'),
    checkDisplay(parser, "/superblock/creator_os", "Linux"),
    checkValue(parser, "/group_desc/group[0]/block_bitmap", 3),
    checkValue(parser, "/group_desc/group[0]/free_blocks_count", 44),
    checkValue(parser, "/group[0]/block_bitmap/item[9]", False),
    checkDisplay(parser, "/group[0]/inode_table/inode[1]/file_type", "Directory"),
    checkValue(parser, "/group[0]/inode_table/inode[11]/size", 1816),
    checkDisplay(parser, "/group[0]/inode_table/inode[11]/ctime", u'2006-12-04 23:22:00'),
)

def checkArticle01(parser): return (
    checkDisplay(parser, "/header/red_mask", u'0x00ff0000'),
    checkDisplay(parser, "/header/color_space", "Business (Saturation)"),
    checkValue(parser, "/pixels/line[94]/pixel[11]", 15265520),
)

def checkReiserFS3(parser): return (
    checkValue(parser, "/superblock/root_block", 645),
    checkDisplay(parser, "/superblock/hash_function", "R5_HASH"),
    checkValue(parser, "/superblock/tree_height", 3),
)

def checkLaraCroft(parser): return (
    checkDesc(parser, "/palette_4bits/color[8]", "RGB color: #100000"),
    checkDesc(parser, "/palette_8bits/color[0]", "RGB color: Black"),
    checkValue(parser, "/compression", 1),
    checkValue(parser, "/horiz_dpi", 500),
)

def checkLinuxSwap(parser): return (
    checkValue(parser, "/version", 1),
    checkValue(parser, "/last_page", 9),
    checkValue(parser, "/magic", u"SWAPSPACE2"),
)

def checkPikachu(parser): return (
    checkValue(parser, "/max_record_size", 510),
    checkValue(parser, "/func[2]/y", 10094),
    checkDisplay(parser, "/func[4]/brush_style", u"Solid"),
    checkValue(parser, "/func[10]/object_id", 2),
)

def checkGlobe(parser): return (
    checkValue(parser, "/file_size", 3923),
    checkValue(parser, "/func[1]/x", 9989),
    checkDisplay(parser, "/func[4]/operation", u"Copy pen (P)"),
    checkDisplay(parser, "/func[9]/brush_style", u"Null"),
)

def checkIndiana(parser): return (
    checkDesc(parser, "/header", u"Multiple tracks, synchronous; 3 tracks"),
    checkDisplay(parser, "/track[0]/command[1]/microsec_quarter", u"300.00 ms"),
    checkDisplay(parser, "/track[1]/command[6]/note", u"A (octave 5)"),
    checkValue(parser, "/track[1]/command[8]/time", 408),
    checkValue(parser, "/track[1]/command[8]/velocity", 80),
)

def checkGrassLogo(parser): return (
    checkValue(parser, "/func[4]/y", 297),
    checkDesc(parser, "/func[15]", u"Begin path"),
    checkDesc(parser, "/func[40]/color", u"RGB color: #008F00 (opacity: 0%)"),
    checkValue(parser, "/emf_header/maj_ver", 1),
    checkValue(parser, "/emf_header/width_px", 1024),
    checkValue(parser, "/emf_header/width_mm", 270),
    checkValue(parser, "/emf_header/description", "Adobe Illustrator EMF 8.0"),
)

testcase_files = (
    (u"yellowdude.3ds", checkYellowdude),
    (u"logo-Kubuntu.png", checkLogoUbuntu),
    (u"mbr_linux_and_ext", checkMBR),
    (u"KDE_Click.wav", checkClick),
    (u"test.txt.gz", checkGzip),
    (u"flashmob.mkv", checkFlashMob),
    (u"10min.mkv", check10min),
    (u"CD_0008_5C48_1m53s.cda", checkCDA),
    (u"wormux_32x32_16c.ico", checkWormuxICO),
    (u"audio_8khz_8bit_ulaw_4s39.au", checkAU),
    (u"sheep_on_drugs.mp3", checkSheepMP3),
    (u"pyc_example_1.5.2.pyc", checkPYC),
    (u"pyc_example_2.2.3.pyc", checkPYC),
    (u"pyc_example_2.5c1.pyc", checkPYC),
    (u"ftp-0.17-537.i586.rpm", checkRPM),
    (u"jpeg.exif.photoshop.jpg", checkJPEG),
    (u"small_text.tar", checkTAR),
    (u"cacert_class3.der", checkCACertClass3),
    (u"kde_haypo_corner.bmp", checkCornerBMP),
    (u"steganography.mp3", checkSteganography),
    (u"ReferenceMap.class", checkReferenceMapClass),
    (u"claque-beignet.swf", checkClaqueBeignet),
    (u"breakdance.flv", checkBreakdance),
    (u"arp_dns_ping_dns.tcpdump", checkArpDnsPingDns),
    (u"my60k.ext2", checkExt2),
    (u"article01.bmp", checkArticle01),
    (u"reiserfs_v3_332k.bin", checkReiserFS3),
    (u"lara_croft.pcx", checkLaraCroft),
    (u"linux_swap_9pages", checkLinuxSwap),
    (u"pikachu.wmf", checkPikachu),
    (u"globe.wmf", checkGlobe),
    (u"indiana.mid", checkIndiana),
    (u"grasslogo_vector.emf", checkGrassLogo),
)

def checkFile(filename, check_parser):
    sys.stdout.write("  - Create parser: ")
    sys.stdout.flush()
    try:
        parser = createParser(filename)
    except InputStreamError, err:
        sys.stdout.write("stream error! %s\n" % unicode(err))
        sys.exit(1)
    if not parser:
        sys.stdout.write("unable to create parser\n")
        return False
    sys.stdout.write("ok\n")
    return all(check_parser(parser))

def testFiles(directory):
    if not os.path.exists(directory):
        try:
            os.mkdir(directory)
        except OSError:
             print "Unable to create directory: %s" % directory
             return False

    for filename, check_parser in testcase_files:
        fullname = os.path.join(directory, filename)
        try:
            os.stat(fullname)
        except OSError:
            print >>sys.stderr, \
                "[!] Error: file %s is missing, " \
                "use script %s to fix your testcase" % \
                (filename, DOWNLOAD_SCRIPT)
            return False

        print "[+] Test %s:" % filename
        if not checkFile(fullname, check_parser):
            return False
    return True

def main():
    setlocale(LC_ALL, "C")
    if len(sys.argv) != 2:
        print >>sys.stderr, "usage: %s testcase_directory" % sys.argv[0]
        sys.exit(1)
    charset = getTerminalCharset()
    directory = unicode(sys.argv[1], charset)

    print "Test hachoir-parser using testcase."
    print
    print "Testcase is in directory: %s" % directory
    ok = testFiles(directory)
    if ok:
        print
        print "Result: ok for the %s files" % len(testcase_files)
        sys.exit(0)
    else:
        print
        for index in xrange(3):
            print "!!! ERROR !!!"
        print
        sys.exit(1)

if __name__ == "__main__":
    main()
