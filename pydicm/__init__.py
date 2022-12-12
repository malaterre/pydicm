from pydicm import lowlevel  # FIXME: hide me

from enum import Enum
import ctypes


class Key:
    """
    Main class for key
    """

    def __init__(self, key: lowlevel._Key):
        self.key = key

    # def __repr__(self):
    #    return "<%s key=%r>" % (type(self).__name__, self.key)

    def __str__(self):
        h = self.key.vr
        l1 = chr(h & 0xFF)
        l2 = chr(h >> 8)
        return "<%08x, %c%c>" % (self.key.tag, l1, l2)


class Parser:
    """A pydicm parser.
    Main class to parse
    """

    def __init__(self):
        """doc."""
        mem = ctypes.POINTER(lowlevel._Parser)()
        ret = lowlevel.dicm_parser_create(ctypes.byref(mem))
        if ret < 0:
            raise MemoryError("internal memory allocation failure")
        self._parser = mem.contents

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        lowlevel.dicm_parser_delete(self._parser)

    def set_input(self, io):
        self._io = lowlevel.IO(io)  # FIXME
        ret = lowlevel.dicm_parser_set_input(self._parser, self._io._io)
        if ret < 0:
            raise ValueError(f"Invalid i/o")

    class EventType(Enum):
        STREAM_START = 0
        STREAM_END = 1
        DATASET_START = 2
        DATASET_END = 3
        ELEMENT_KEY = 4
        FRAGMENT = 5
        ELEMENT_VALUE = 6
        ITEM_START = 7
        ITEM_END = 8
        SEQUENCE_START = 9
        SEQUENCE_END = 10

    def next_event(self):
        etype = lowlevel.dicm_parser_next_event(self._parser)
        if etype < 0:
            raise ValueError(f"Invalid Event Type: {etype}")
        return Parser.EventType(etype)

    def key(self):
        tmp = lowlevel._Key()
        ret = lowlevel.dicm_parser_get_key(self._parser, ctypes.byref(tmp))
        if ret < 0:
            raise ValueError(f"Invalid key: {ret}")
        return Key(tmp)

    def value_length(self):
        tmp = ctypes.c_size_t(0)
        ret = lowlevel.dicm_parser_get_value_length(self._parser, ctypes.byref(tmp))
        if ret < 0:
            raise ValueError(f"Invalid value length: {ret}")
        return tmp.value

    def read_value(self, size):
        ba = bytearray(size)
        byte_array = ctypes.c_ubyte * len(ba)
        ret = lowlevel.dicm_parser_read_value(
            self._parser, byte_array.from_buffer(ba), len(ba)
        )
        if ret < 0:
            raise ValueError(f"Invalid value: {ret}")
        return ba
