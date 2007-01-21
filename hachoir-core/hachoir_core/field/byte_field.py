"""
Very basic field: raw content with a size in byte. Use this class for
unknown content.
"""

from hachoir_core.field import Field, FieldError
from hachoir_core.tools import makePrintable
from hachoir_core.bits import str2hex
from hachoir_core import config

class RawBytes(Field):
    """
    Byte vector of unknown content

    @see: L{Bytes}
    """
    static_size = staticmethod(lambda *args, **kw: args[1]*8)

    def __init__(self, parent, name, length, description="Raw data"):
        assert issubclass(parent.__class__, Field)
        if not(0 < length):
            raise FieldError("Invalid RawBytes length (%s)!" % length)
        assert length < (1 << 64) # arbitrary limit
        Field.__init__(self, parent, name, length*8, description)
        self._display = None

    def createDisplay(self, human=True):
        max_bytes = config.max_byte_length
        if self._value is None:
            if self._display is None:
                address = self.absolute_address
                length = min(self._size / 8, max_bytes)
                self._display = self._parent.stream.readBytes(address, length)
            display = self._display
        else:
            display = self._value[:max_bytes]
        if human:
            if 8 * len(display) < self._size:
                display += "(...)"
            return makePrintable(display, "latin-1", quote='"', to_unicode=True)
        else:
            display = str2hex(display, format=r"\x%02x")
            if 8 * len(display) < self._size:
                return '"%s(...)"' % display
            else:
                return '"%s"' % display

    def createRawDisplay(self):
        return self.createDisplay(human=False)

    def createValue(self):
        assert (self._size % 8) == 0
        if self._display:
            self._display = None
        return self._parent.stream.readBytes(
            self.absolute_address, self._size / 8)

class Bytes(RawBytes):
    """
    Byte vector: can be used for magic number or GUID/UUID for example.

    @see: L{RawBytes}
    """
    pass
