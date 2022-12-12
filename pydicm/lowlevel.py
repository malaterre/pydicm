"""
Hide all the low level ctypes declarion. We want to have clean:

import pydicm

without any pollution.
"""
import ctypes

from typing import final
import logging

_lib = ctypes.cdll.LoadLibrary("libdicm.so.0")

# resolve and return a libdicm function with the specified properties


def _func(name, restype, argtypes, errcheck=None):
    func = getattr(_lib, name)
    func.restype = restype
    func.argtypes = argtypes
    if errcheck is not None:
        func.errcheck = errcheck
    return func


# logging
FPLOGFUNC = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p)
dicm_configure_log_msg = _func("dicm_configure_log_msg", None, [FPLOGFUNC])

@FPLOGFUNC
def py_log_func(level, msg):
    # https://docs.python.org/3/library/logging.html#levels
    log_levels = {
        0: logging.DEBUG // 2,  # Trace
        1: logging.DEBUG,  # Debug
        2: logging.INFO,  # Information
        3: logging.WARNING,  # Warning
        4: logging.ERROR,  # Error
        5: logging.CRITICAL,  # Critical
        # logging.NOTSET => wotsit ?
    }
    log = logging.getLogger("pydicm")
    log.log(log_levels[level], msg.decode("utf-8"))
    return


# setup default listener:
dicm_configure_log_msg(py_log_func)


@final
class _IO(ctypes.Structure):
    pass


# int (*fp_read)(void *const, void *, size_t),
# int (*fp_seek)(void *const, long, int), /* can be null */
# int (*fp_write)(void *const, const void *, size_t));

FPREADFUNC = ctypes.CFUNCTYPE(
    ctypes.c_int, ctypes.POINTER(_IO), ctypes.c_void_p, ctypes.c_size_t
)
FPSEEKFUNC = ctypes.CFUNCTYPE(
    ctypes.c_int, ctypes.POINTER(_IO), ctypes.c_long, ctypes.c_int
)
FPWRITEFUNC = ctypes.CFUNCTYPE(
    ctypes.c_int, ctypes.POINTER(_IO), ctypes.c_void_p, ctypes.c_size_t
)

# FPREADFUNC = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p , ctypes.c_void_p, ctypes.c_size_t)
# FPSEEKFUNC = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p , ctypes.c_long, ctypes.c_int)
# FPWRITEFUNC = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p , ctypes.c_void_p, ctypes.c_size_t)


@FPREADFUNC
def py_read_func(a, b, c):
    print("read")
    return 0


@FPSEEKFUNC
def py_seek_func(a, b, c):
    print("seek")
    return 0


@FPWRITEFUNC
def py_write_func(a, b, c):
    print("write")
    return 0


dicm_io_create = _func(
    "dicm_create",
    ctypes.c_int,
    [ctypes.POINTER(ctypes.POINTER(_IO)), FPREADFUNC, FPSEEKFUNC, FPWRITEFUNC],
)
dicm_io_delete = _func("dicm_delete", None, [ctypes.POINTER(_IO)])


@final
class _Key(ctypes.Structure):
    _fields_ = [("tag", ctypes.c_uint32), ("vr", ctypes.c_uint32)]


@final
class _Parser(ctypes.Structure):
    pass


dicm_parser_create = _func(
    "dicm_parser_create", ctypes.c_int, [ctypes.POINTER(ctypes.POINTER(_Parser))]
)
dicm_parser_set_input = _func(
    "dicm_parser_set_input",
    ctypes.c_int,
    [ctypes.POINTER(_Parser), ctypes.POINTER(_IO)],
)
dicm_parser_next_event = _func(
    "dicm_parser_next_event", ctypes.c_int, [ctypes.POINTER(_Parser)]
)
dicm_parser_get_key = _func(
    "dicm_parser_get_key", ctypes.c_int, [ctypes.POINTER(_Parser), ctypes.POINTER(_Key)]
)

dicm_parser_get_value_length = _func(
    "dicm_parser_get_value_length",
    ctypes.c_int,
    [ctypes.POINTER(_Parser), ctypes.POINTER(ctypes.c_size_t)],
)

dicm_parser_read_value = _func(
    "dicm_parser_read_value",
    ctypes.c_int,
    [ctypes.POINTER(_Parser), ctypes.c_void_p, ctypes.c_size_t],
)

dicm_parser_delete = _func("dicm_delete", None, [ctypes.POINTER(_Parser)])


class IO:
    """IO wrapper to python file-object"""

    def __init__(self, file_object):
        """doc."""
        mem = ctypes.POINTER(_IO)()
        # I need to keep a reference to callbacks to prevent gc:
        # https://stackoverflow.com/questions/74517129/garbage-collection-in-python-module
        self._read = self._getReadCallbackFunc()
        self._seek = py_seek_func
        self._write = py_write_func
        ret = dicm_io_create(ctypes.byref(mem), self._read, self._seek, self._write)
        if ret < 0:
            raise MemoryError("internal memory allocation failure")
        self._io = mem.contents
        self.file_object = file_object

    def _getReadCallbackFunc(self):  # type: ignore
        """Callback from python layer to C layer"""

        # simply implementation, instead of poking around with io pointer,
        # simply use a method instead of a function
        # https://stackoverflow.com/questions/3245859/back-casting-a-ctypes-py-object-in-a-callback
        @FPREADFUNC
        def my_read_func(io, buf, size):
            # FIXME: readinto ?
            tmp = self.file_object.read(size)  # bytearray
            if len(tmp) != 0:
                # https://stackoverflow.com/questions/68075730/converting-a-ctypes-c-void-p-and-ctypes-c-size-t-to-bytearray-or-string
                b = ctypes.cast(buf, ctypes.POINTER(ctypes.c_ubyte * size)).contents
                ctypes.memmove(b, tmp, len(tmp))
                return len(tmp)
            return 0

        return my_read_func

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        dicm_io_delete(self._io)
