"""Read taskbar button bounds through Windows UI Automation (no injection).

COM stays on the discovery worker. No accessibility names or personal data are read.
"""
import ctypes as C
from ctypes import wintypes as W
import uuid

ole = C.OleDLL("ole32")
auto = C.OleDLL("oleaut32")
PTR = C.c_void_p


class GUID(C.Structure):
    _fields_ = [("bytes", C.c_ubyte * 16)]

    def __init__(self, value):
        super().__init__()
        self.bytes[:] = uuid.UUID(value).bytes_le


class Value(C.Union):
    _fields_ = [("integer", C.c_long), ("pointer", PTR), ("storage", C.c_ubyte * 16)]


class Variant(C.Structure):
    _fields_ = [("vt", C.c_ushort), ("r1", C.c_ushort), ("r2", C.c_ushort),
                ("r3", C.c_ushort), ("value", Value)]


def method(ptr, index, result, *args):
    table = C.cast(ptr, C.POINTER(C.POINTER(PTR))).contents
    return C.WINFUNCTYPE(result, PTR, *args)(table[index])


def call(ptr, index, *typed):
    types, values = zip(*typed) if typed else ((), ())
    result = method(ptr, index, C.c_long, *types)(ptr, *values)
    if result < 0:
        raise OSError(f"UI Automation HRESULT {result & 0xffffffff:08x}")


def release(ptr):
    if ptr:
        method(ptr, 2, W.ULONG)(ptr)


ole.CoInitializeEx.argtypes = [PTR, W.DWORD]
ole.CoCreateInstance.argtypes = [C.POINTER(GUID), PTR, W.DWORD, C.POINTER(GUID), C.POINTER(PTR)]
auto.VariantClear.argtypes = [C.POINTER(Variant)]
auto.SafeArrayAccessData.argtypes = [PTR, C.POINTER(PTR)]
auto.SafeArrayUnaccessData.argtypes = [PTR]
auto.SafeArrayGetLBound.argtypes = [PTR, W.UINT, C.POINTER(C.c_long)]
auto.SafeArrayGetUBound.argtypes = [PTR, W.UINT, C.POINTER(C.c_long)]


def property_value(element, property_id):
    value = Variant()
    call(element, 10, (C.c_int, property_id), (C.POINTER(Variant), C.byref(value)))
    return value


def button_bounds(hwnd: int):
    ole.CoInitializeEx(None, 0)
    client, root, condition, elements = PTR(), PTR(), PTR(), PTR()
    result = []
    try:
        ole.CoCreateInstance(C.byref(GUID("ff48dba4-60ef-4201-aa87-54103eef594e")), None, 1,
                             C.byref(GUID("30cbe57d-d9d0-452a-ab13-7ac5ac4825ee")), C.byref(client))
        call(client, 6, (W.HWND, hwnd), (C.POINTER(PTR), C.byref(root)))
        call(client, 21, (C.POINTER(PTR), C.byref(condition)))
        call(root, 6, (C.c_int, 4), (PTR, condition), (C.POINTER(PTR), C.byref(elements)))
        count = C.c_int()
        call(elements, 3, (C.POINTER(C.c_int), C.byref(count)))
        for index in range(min(count.value, 512)):
            element = PTR()
            call(elements, 4, (C.c_int, index), (C.POINTER(PTR), C.byref(element)))
            try:
                kind = property_value(element, 30003)
                control_type = kind.value.integer if kind.vt == 3 else 0
                auto.VariantClear(C.byref(kind))
                if control_type not in (50000, 50007, 50011, 50013, 50031):
                    continue
                bounds = property_value(element, 30001)
                try:
                    if bounds.vt == 0x2005:
                        lower, upper = C.c_long(), C.c_long()
                        array = bounds.value.pointer
                        auto.SafeArrayGetLBound(array, 1, C.byref(lower))
                        auto.SafeArrayGetUBound(array, 1, C.byref(upper))
                        if upper.value - lower.value + 1 == 4:
                            data = PTR()
                            auto.SafeArrayAccessData(array, C.byref(data))
                            try:
                                x, y, width, height = C.cast(data, C.POINTER(C.c_double * 4)).contents
                                if width > 0 and height > 0:
                                    result.append((round(x), round(y), round(x + width), round(y + height)))
                            finally:
                                auto.SafeArrayUnaccessData(array)
                finally:
                    auto.VariantClear(C.byref(bounds))
            finally:
                release(element)
        return result
    finally:
        for obj in (elements, condition, root, client):
            release(obj)
        ole.CoUninitialize()
