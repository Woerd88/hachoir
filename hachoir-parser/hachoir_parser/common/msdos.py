"""
MS-DOS structures.

Documentation:
- File attributes:
  http://www.cs.colorado.edu/~main/cs1300/include/ddk/winddk.h
"""

from hachoir_core.field import StaticFieldSet
from hachoir_core.field import Bit, NullBits

class MSDOSFileAttr(StaticFieldSet):
    """
    Decodes the MSDOS file attribute
    """
    format = (
        (Bit, "read_only"),
        (Bit, "hidden"),
        (Bit, "system"),
        (NullBits, "reserved[]", 1),
        (Bit, "directory"),
        (Bit, "archive"),
        (Bit, "device"),
        (Bit, "normal"),
        (Bit, "temporary"),
        (Bit, "sparse_file"),
        (Bit, "reparse_file"),
        (Bit, "compressed"),
        (Bit, "offline"),
        (Bit, "dont_index_content"),
        (Bit, "encrypted"),
        (NullBits, "reserved[]", 17),
    )
    _text_keys = ("directory", "read_only", "compressed", "hidden", "system",
        "normal", "device", "temporary")

    def createText(self):
        mode = []
        for name in self._text_keys:
            if self[name].value:
                mode.append(name)
        return ", ".join(mode)

