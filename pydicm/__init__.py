from pydicm import lowlevel  # FIXME: hide me

import ctypes


class IO:
    """A pydicm parser.
    Main class to parse
    """

    def __init__(self, file_object):
        """doc."""
        mem = ctypes.POINTER(lowlevel._IO)()
        self._read = self._getReadCallbackFunc()
        self._seek = lowlevel.py_seek_func
        self._write = lowlevel.py_write_func
        ret = lowlevel.dicm_io_create(
            ctypes.byref(mem), self._read, self._seek, self._write
        )
        if ret < 0:
            raise MemoryError("internal memory allocation failure")
        self._io = mem.contents
        self.file_object = file_object

    def _getReadCallbackFunc(self):  # type: ignore
        """Callback from python layer to C layer"""

        @lowlevel.FPREADFUNC
        def my_read_func(io, buf, size):
            # FIXME: too many copies:
            tmp = self.file_object.read(size)  # bytearray
            assert len(tmp) == size or len(tmp) == 0
            if len(tmp) != 0:
                cbytearray = ctypes.c_uint8 * size
                byte_arr = cbytearray.from_buffer_copy(tmp)
                ctypes.memmove(buf, byte_arr, len(tmp))
                return len(tmp)
            return 0

        return my_read_func

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        lowlevel.dicm_io_delete(self._io)


class Key:
    """
    Main class for key
    """

    def __init__(self, key):
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
        # self._parser = mem[0]
        self._parser = mem.contents

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        lowlevel.dicm_parser_delete(self._parser)

    def set_input(self, io):
        lowlevel.dicm_parser_set_input(self._parser, io._io)

    def next_event(self):
        return lowlevel.dicm_parser_next_event(self._parser)

    def key(self):
        tmp = lowlevel._Key()
        lowlevel.dicm_parser_get_key(self._parser, ctypes.byref(tmp))
        return Key(tmp)

    def value_length(self):
        tmp = ctypes.c_size_t(0)
        ret = lowlevel.dicm_parser_get_value_length(self._parser, ctypes.byref(tmp))
        return tmp.value

    def read_value(self, size):
        ba = bytearray(size)
        byte_array = ctypes.c_uint8 * len(ba)
        lowlevel.dicm_parser_read_value(
            self._parser, byte_array.from_buffer(ba), len(ba)
        )
        return ba


DICM_STREAM_START_EVENT = 0
DICM_STREAM_END_EVENT = 1
DICM_DATASET_START_EVENT = 2
DICM_DATASET_END_EVENT = 3
DICM_ELEMENT_KEY_EVENT = 4
DICM_FRAGMENT_EVENT = 5
DICM_ELEMENT_VALUE_EVENT = 6
DICM_ITEM_START_EVENT = 7
DICM_ITEM_END_EVENT = 8
DICM_SEQUENCE_START_EVENT = 9
DICM_SEQUENCE_END_EVENT = 10
