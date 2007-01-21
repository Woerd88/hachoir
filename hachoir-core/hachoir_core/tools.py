# -*- coding: utf-8 -*-

"""
Various utilities.
"""

from hachoir_core.i18n import _, ngettext
import re
import stat
from math import floor, ceil
from datetime import datetime, timedelta

def paddingSize(value, align):
    """
    Compute size of a padding field.

    >>> paddingSize(31, 4)
    1
    >>> paddingSize(32, 4)
    0
    >>> paddingSize(33, 4)
    3

    Note: (value + paddingSize(value, align)) == alignValue(value, align)
    """
    if value % align != 0:
        return align - (value % align)
    else:
        return 0

def alignValue(value, align):
    """
    Align a value to next 'align' multiple.

    >>> alignValue(31, 4)
    32
    >>> alignValue(32, 4)
    32
    >>> alignValue(33, 4)
    36

    Note: alignValue(value, align) == (value + paddingSize(value, align))
    """

    if value % align != 0:
        return value + align - (value % align)
    else:
        return value

def humanDurationNanosec(nsec):
    """
    Convert a duration in nanosecond to human natural representation.
    Returns an unicode string.

    >>> humanDurationNanosec(60417893)
    u'60.42 ms'
    """

    # Nano second
    if nsec < 1000:
        return u"%u nsec" % nsec

    # Micro seconds
    usec, nsec = divmod(nsec, 1000)
    if usec < 1000:
        return u"%.2f usec" % (usec+float(nsec)/1000)

    # Milli seconds
    msec, usec = divmod(usec, 1000)
    if msec < 1000:
        return u"%.2f ms" % (msec + float(usec)/1000)
    return humanDuration(msec)

def humanDuration(millisec):
    """
    Convert a duration in millisecond to human natural representation.
    Returns an unicode string.

    >>> humanDuration(213)
    u'213 ms'
    >>> humanDuration(4213)
    u'4.21 sec'
    >>> humanDuration(6402309)
    u'1 hour(s) 46 min 42 sec'
    """
    # Milliseconds
    if millisec < 1000:
        return u"%u ms" % millisec

    # Seconds
    second, millisec = divmod(millisec, 1000)
    if second < 60:
        return  u"%.2f sec" % (second+float(millisec)/1000)

    # Minutes
    minute, second = divmod(second, 60)
    if minute < 60:
        return u"%u min %u sec" % (minute, second)

    # Hours
    hour, minute = divmod(minute, 60)
    if hour < 24:
        if 0 < second:
            return u"%u hour(s) %u min %u sec" % (hour, minute, second)
        else:
            return u"%u hour(s) %u min" % (hour, minute)

    # Days
    day, hour = divmod(hour, 24)
    if day < 365:
        return u"%u day(s) %u hour(s)" % (day, hour)

    # Years
    year, day = divmod(day, 365)
    if day != 0:
        text = u"%u year(s) %u day(s)" % (year, day)
    else:
        text = u"%u year(s)" % (year)
    return text

def humanFilesize(size):
    """
    Convert a file size in byte to human natural representation.
    It uses the values: 1 KB is 1024 bytes, 1 MB is 1024 KB, etc.
    The result is an unicode string.

    >>> humanFilesize(1)
    u'1 byte'
    >>> humanFilesize(790)
    u'790 bytes'
    >>> humanFilesize(256960)
    u'250.9 KB'
    """
    if size < 10000:
        return ngettext("%u byte", "%u bytes", size) % size
    units = [_("KB"), _("MB"), _("GB"), _("TB")]
    size = float(size)
    divisor = 1024
    for unit in units:
        size = size / divisor
        if size < divisor:
            return "%.1f %s" % (size, unit)
    return "%u %s" % (size, unit)

def humanBitSize(size):
    """
    Convert a size in bit to human classic representation.
    It uses the values: 1 Kbit is 1000 bits, 1 Mbit is 1000 Kbit, etc.
    The result is an unicode string.

    >>> humanBitSize(1)
    u'1 bit'
    >>> humanBitSize(790)
    u'790 bits'
    >>> humanBitSize(256960)
    u'257.0 Kbit'
    """
    divisor = 1000
    if size < divisor:
        return ngettext("%u bit", "%u bits", size) % size
    units = [u"Kbit", u"Mbit", u"Gbit", u"Tbit"]
    size = float(size)
    for unit in units:
        size = size / divisor
        if size < divisor:
            return "%.1f %s" % (size, unit)
    return u"%u %s" % (size, unit)

def humanBitRate(size):
    """
    Convert a bit rate to human classic representation. It uses humanBitSize()
    to convert size into human reprensation. The result is an unicode string.

    >>> humanBitRate(790)
    u'790 bits/sec'
    >>> humanBitRate(256960)
    u'257.0 Kbit/sec'
    """
    return "".join((humanBitSize(size), "/sec"))

def humanFrequency(hertz):
    """
    Convert a frequency in hertz to human classic representation.
    It uses the values: 1 KHz is 1000 Hz, 1 MHz is 1000 KMhz, etc.
    The result is an unicode string.

    >>> humanFrequency(790)
    u'790 Hz'
    >>> humanFrequency(629469)
    u'629.5 KHz'
    """
    divisor = 1000
    if hertz < divisor:
        return u"%u Hz" % hertz
    units = [u"KHz", u"MHz", u"GHz", u"THz"]
    hertz = float(hertz)
    for unit in units:
        hertz = hertz / divisor
        if hertz < divisor:
            return u"%.1f %s" % (hertz, unit)
    return u"%s %s" % (hertz, unit)

regex_control_code = re.compile("([\x00-\x1f\x7f])")
controlchars = tuple({
        # Don't use "\0", because "\0"+"0"+"1" = "\001" = "\1" (1 character)
        # Same rease to not use octal syntax ("\1")
        ord("\n"): r"\n",
        ord("\r"): r"\r",
        ord("\t"): r"\t",
        ord("\a"): r"\a",
        ord("\b"): r"\b",
    }.get(code, '\\x%02x' % code)
    for code in xrange(128)
)

def makePrintable(data, charset, quote=None, to_unicode=False, smart=True):
    r"""
    Prepare a string to make it printable in the specified charset.
    It escapes control caracters. Caracter with code bigger than 127
    are escapped if: data type is 'str' or if charset is "ASCII".

    Examples with Unicode:
    >>> aged = unicode("âgé", "UTF-8")
    >>> repr(aged)  # text type is 'unicode'
    "u'\\xe2g\\xe9'"
    >>> makePrintable("abc\0", "UTF-8")
    'abc\\0'
    >>> makePrintable(aged, "latin1")
    '\xe2g\xe9'
    >>> makePrintable(aged, "latin1", quote='"')
    '"\xe2g\xe9"'

    Examples with string encoded in latin1:
    >>> aged_latin = unicode("âgé", "UTF-8").encode("latin1")
    >>> repr(aged_latin)  # text type is 'str'
    "'\\xe2g\\xe9'"
    >>> makePrintable(aged_latin, "latin1")
    '\\xe2g\\xe9'
    >>> makePrintable("", "latin1")
    ''
    >>> makePrintable("a", "latin1", quote='"')
    '"a"'
    >>> makePrintable("", "latin1", quote='"')
    '(empty)'
    >>> makePrintable("abc", "latin1", quote="'")
    "'abc'"

    Control codes:
    >>> makePrintable("\0\x03\x0a\x10 \x7f", "latin1")
    '\\0\\3\\n\\x10 \\x7f'

    Quote character may also be escaped (only ' and "):
    >>> print makePrintable("a\"b", "latin-1", quote='"')
    "a\"b"
    >>> print makePrintable("a\"b", "latin-1", quote="'")
    'a"b'
    >>> print makePrintable("a'b", "latin-1", quote="'")
    'a\'b'
    """

    if data:
        if not isinstance(data, unicode):
            data = unicode(data, "ISO-8859-1")
            charset = "ascii"
        data = regex_control_code.sub(
            lambda regs: controlchars[ord(regs.group(1))], data)
        if quote:
            if quote in "\"'":
                data = data.replace(quote, '\\' + quote)
            data = ''.join((quote, data, quote))
    elif quote:
        data = "(empty)"
    data = data.encode(charset, "backslashreplace")
    if smart:
        # Replace \x00\x01 by \0\1
        data = re.sub(r"\\x0([0-7])(?=[^0-7]|$)", r"\\\1", data)
    if to_unicode:
        data = unicode(data, charset)
    return data

def binarySearch(seq, cmp_func):
    """
    Search a value in a sequence using binary search. Returns index of the
    value, or None if the value doesn't exist.

    'seq' have to be sorted in ascending order according to the
    comparaison function ;

    'cmp_func', prototype func(x), is the compare function:
    - Return strictly positive value if we have to search forward ;
    - Return strictly negative value if we have to search backward ;
    - Otherwise (zero) we got the value.

    >>> # Search number 5 (search forward)
    ... binarySearch([0, 4, 5, 10], lambda x: 5-x)
    2
    >>> # Backward search
    ... binarySearch([10, 5, 4, 0], lambda x: x-5)
    1
    """
    lower = 0
    upper = len(seq)
    while lower < upper:
        index = (lower + upper) >> 1
        diff = cmp_func(seq[index])
        if diff < 0:
            upper = index
        elif diff > 0:
            lower = index + 1
        else:
            return index
    return None

def lowerBound(seq, cmp_func):
    f = 0
    l = len(seq)
    while l > 0:
        h = l >> 1
        m = f + h
        if cmp_func(seq[m]):
            f = m
            f += 1
            l -= h + 1
        else:
            l = h
    return f

def humanUnixAttributes(mode):
    """
    Convert a Unix file attributes (or "file mode") to a string.

    Original source code:
    http://cvs.savannah.gnu.org/viewcvs/coreutils/lib/filemode.c?root=coreutils

    >>> humanUnixAttributes(0644)
    '-rw-r--r-- (644)'
    >>> humanUnixAttributes(02755)
    '-rwxr-sr-x (2755)'
    """

    def ftypelet(mode):
        if stat.S_ISREG (mode) or not stat.S_IFMT(mode):
            return '-'
        if stat.S_ISBLK (mode): return 'b'
        if stat.S_ISCHR (mode): return 'c'
        if stat.S_ISDIR (mode): return 'd'
        if stat.S_ISFIFO(mode): return 'p'
        if stat.S_ISLNK (mode): return 'l'
        if stat.S_ISSOCK(mode): return 's'
        return '?'

    chars = [ ftypelet(mode), 'r', 'w', 'x', 'r', 'w', 'x', 'r', 'w', 'x' ]
    for i in xrange(1, 10):
        if not mode & 1 << 9 - i:
            chars[i] = '-'
    if mode & stat.S_ISUID:
        if chars[3] != 'x':
            chars[3] = 'S'
        else:
            chars[3] = 's'
    if mode & stat.S_ISGID:
        if chars[6] != 'x':
            chars[6] = 'S'
        else:
            chars[6] = 's'
    if mode & stat.S_ISVTX:
        if chars[9] != 'x':
            chars[9] = 'T'
        else:
            chars[9] = 't'
    return "%s (%o)" % (''.join(chars), mode)

def createDict(data, index):
    """
    Create a new dictionnay from dictionnary key=>values:
    just keep value number 'index' from all values.

    >>> data={10: ("dix", 100, "a"), 20: ("vingt", 200, "b")}
    >>> createDict(data, 0)
    {10: 'dix', 20: 'vingt'}
    >>> createDict(data, 2)
    {10: 'a', 20: 'b'}
    """
    return dict( (key,values[index]) for key, values in data.iteritems() )

# Start of UNIX timestamp (Epoch): 1st January 1970 at 00:00
UNIX_TIMESTAMP_T0 = datetime(1970, 1, 1)

def timestampUNIX(value):
    """
    Convert an UNIX (32-bit) timestamp to datetime object. Timestamp value
    is the number of seconds since the 1st January 1970 at 00:00. Maximum
    value is 2147483647: 19 january 2038 at 03:14:07.

    May raise ValueError for invalid value: value have to be in 0..2147483647.

    >>> timestampUNIX(0)
    datetime.datetime(1970, 1, 1, 0, 0)
    >>> timestampUNIX(1154175644)
    datetime.datetime(2006, 7, 29, 12, 20, 44)
    >>> timestampUNIX(1154175644.37)
    datetime.datetime(2006, 7, 29, 12, 20, 44, 370000)
    >>> timestampUNIX(2147483647)
    datetime.datetime(2038, 1, 19, 3, 14, 7)
    """
    if not isinstance(value, (float, int, long)):
        raise TypeError("timestampUNIX(): an integer or float is required")
    if not(0 <= value <= 2147483647):
        raise ValueError("timestampUNIX(): value have to be in 0..2147483647")
    return UNIX_TIMESTAMP_T0 + timedelta(seconds=value)

def humanDatetime(value):
    """
    Convert a timestamp to Unicode string: use ISO format with space separator.

    >>> humanDatetime( datetime(2006, 7, 29, 12, 20, 44) )
    u'2006-07-29 12:20:44'
    >>> humanDatetime( datetime(2003, 6, 30, 16, 0, 5, 370000) )
    u'2003-06-30 16:00:05.370000'
    """
    return unicode(value.isoformat().replace('T', ' '))
