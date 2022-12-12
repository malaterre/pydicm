"""
Hide all the low level ctypes declarion. We want to have clean:

import pydicm

without any pollution.
"""
import ctypes

# from ctypes import *
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
