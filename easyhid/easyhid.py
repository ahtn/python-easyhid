#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2017 jem@seethis.link
# Licensed under the MIT license (http://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function, unicode_literals

import cffi
import ctypes.util
import platform

ffi = cffi.FFI()
ffi.cdef("""
struct hid_device_info {
    char *path;
    unsigned short vendor_id;
    unsigned short product_id;
    wchar_t *serial_number;
    unsigned short release_number;
    wchar_t *manufacturer_string;
    wchar_t *product_string;
    unsigned short usage_page;
    unsigned short usage;
    int interface_number;
    struct hid_device_info *next;
};
typedef struct hid_device_ hid_device;

int hid_init(void);
int hid_exit(void);
struct hid_device_info* hid_enumerate(unsigned short, unsigned short);
void hid_free_enumeration (struct hid_device_info *devs);
hid_device* hid_open (unsigned short vendor_id, unsigned short product_id, const wchar_t *serial_number);
hid_device* hid_open_path (const char *path);
int hid_write (hid_device *device, const unsigned char *data, size_t length);
int hid_read_timeout (hid_device *dev, unsigned char *data, size_t length, int milliseconds);
int hid_read (hid_device *device, unsigned char *data, size_t length);
int hid_set_nonblocking (hid_device *device, int nonblock);
int hid_send_feature_report (hid_device *device, const unsigned char *data, size_t length);
int hid_get_feature_report (hid_device *device, unsigned char *data, size_t length);
void hid_close (hid_device *device);
int hid_get_manufacturer_string (hid_device *device, wchar_t *string, size_t maxlen);
int hid_get_product_string (hid_device *device, wchar_t *string, size_t maxlen);
int hid_get_serial_number_string (hid_device *device, wchar_t *string, size_t maxlen);
int hid_get_indexed_string (hid_device *device, int string_index, wchar_t *string, size_t maxlen);
const wchar_t* hid_error (hid_device *device);
""")

if "Windows" in platform.platform():
    try:
        hidapi = ffi.dlopen('hidapi.dll')
    except:
        hidapi = ffi.dlopen(ctypes.util.find_library('hidapi.dll'))
elif "Darwin" in platform.platform():
    try:
        hidapi = ffi.dlopen('hidapi')
    except:
        hidapi = ffi.dlopen(ctypes.util.find_library('hidapi'))
else:
    try:
        hidapi = ffi.dlopen('hidapi-libusb')
    except:
        hidapi = ffi.dlopen(ctypes.util.find_library('hidapi-libusb'))

def _c_to_py_str(val):
    if val == ffi.NULL:
        return None

    new_val = ffi.string(val)
    if type(new_val) == bytes or type(new_val) == bytearray:
        return new_val.decode("utf-8")
    else:
        return new_val

class HIDException(Exception):
    pass

class HIDDevice(object):
    """
    A HID device for communication with a HID interface.

    Should normally be created through an Enumeration object.
    """

    def __init__(self, cdata):
        if cdata == ffi.NULL:
            raise TypeError
        self.path = _c_to_py_str(cdata.path)
        self.vendor_id = cdata.vendor_id
        self.product_id = cdata.product_id
        self.release_number = cdata.release_number
        self.manufacturer_string = _c_to_py_str(cdata.manufacturer_string)
        self.product_string = _c_to_py_str(cdata.product_string)
        self.serial_number = _c_to_py_str(cdata.serial_number)
        self.usage_page = cdata.usage_page
        self.usage = cdata.usage
        self.interface_number = cdata.interface_number

        self._device = None
        self._is_open = False

    def __del__(self):
        self.close()

    def __enter__(self):
        self.open()

    def __exit__(self, err_type, err_value, traceback):
        self.close()

    def open(self):
        """
        Open the HID device for reading and writing.
        """
        if self._is_open:
            raise HIDException("Failed to open device: HIDDevice already open")

        path = self.path.encode('utf-8')
        dev = hidapi.hid_open_path(path)

        if dev:
            self._is_open = True
            self._device = dev
        else:
            raise HIDException("Failed to open device")


    def close(self):
        """
        Closes the hid device
        """
        if self._is_open:
            self._is_open = False
            hidapi.hid_close(self._device)

    def write(self, data, report_id=0):
        """
        Writes data to the HID device on its endpoint.

        Parameters:
            data: data to send on the HID endpoint
            report_id: the report ID to use.

        Returns:
            The number of bytes written including the report ID.
        """

        if not self._is_open:
            raise HIDException("HIDDevice not open")

        write_data = bytes([report_id]) + bytes(data)
        cdata = ffi.new("const unsigned char[]", write_data)
        num_written = hidapi.hid_write(self._device, cdata, len(write_data))
        if num_written < 0:
            raise HIDException("Failed to write to HID device: " + str(num_written))
        else:
            return num_written

    def read(self, size=64, timeout=None):
        """
        Read from the hid device on its endpoint.


        Parameters:
            size: number of bytes to read
            timeout: length to wait in milliseconds

        Returns:
            The HID report read from the device. The first byte in the result
            will be the report ID if used.
        """

        if not self._is_open:
            raise HIDException("HIDDevice not open")

        data = [0] * size
        cdata = ffi.new("unsigned char[]", data)
        bytes_read = 0

        if timeout == None:
            bytes_read = hidapi.hid_read(self._device, cdata, len(cdata))
        else:
            bytes_read = hidapi.hid_read_timeout(self._device, cdata, len(cdata), timeout)


        if bytes_read < 0:
            raise HIDException("Failed to read from HID device: " + str(bytes_read))
        elif bytes_read == 0:
            return []
        else:
            return bytearray(cdata)

    def set_nonblocking(self, enable_nonblocking):
        if not self._is_open:
            raise HIDException("HIDDevice not open")

        if type(enable_nonblocking) != bool:
            raise TypeError
        hidapi.hid_set_nonblocking(self._device, enable_nonblocking)

    def is_open(self):
        """Check if the HID device is open"""
        return self._is_open

    def is_connected(self):
        """
        Checks if the USB device is still connected
        """
        if self._is_open:
            err = hidapi.hid_read_timeout(self._device, ffi.NULL, 0, 0)
            if err == -1:
                return False
            else:
                return True
        else:
            en = Enumeration(vid=self.vendor_id, pid=self.product_id).find(path=self.path)
            if len(en) == 0:
                return False
            else:
                return True

    def send_feature_report(self, data, report_id=0x00):
        """
        Send a Feature report to a HID device.

        Feature reports are sent over the Control endpoint as a Set_Report
        transfer.

        Parameters:
            data    The data to send

        Returns:
            This function returns the actual number of bytes written
        """
        if not self._is_open:
            raise HIDException("HIDDevice not open")

        report = bytes([report_id]) + bytes(data)
        cdata = ffi.new("const unsigned char[]", report)
        bytes_read = hidapi.hid_send_feature_report(self._device, cdata, len(report))

        if bytes_read == -1:
            raise HIDException("Failed to send feature report to HID device")

        return bytes_read

    def get_feature_report(self, size=64, report_id=0x00):
        """
        Get a feature report from a HID device.

        Feature reports are sent over the Control endpoint as a Get_Report
        transfer.

        Parameters:
            size        The number of bytes to read.
            report_id   The report id to read

        Returns:
            They bytes read from the HID report
        """
        cdata = ffi.new("unsigned char[{}]".format(size+1))
        cdata[0] = report_id
        bytes_read = hidapi.hid_get_feature_report(self._device, cdata, size+1)

        if bytes_read == -1:
            raise HIDException("Failed to get feature report from HID device")

        return bytearray(cdata[1:size+1])

    def get_error(self):
        """
        Get an error string from the device
        """
        err_str = hidapi.hid_error(self._device)
        if err_str == ffi.NULL:
            return None
        else:
            return ffi.string(err_str)

    def _get_prod_string_common(self, hid_fn):
        max_len = 128
        str_buf = ffi.new("wchar_t[]", bytearray(max_len).decode('utf-8'))
        ret = hid_fn(self._device, str_buf, max_len)
        if ret < 0:
            raise HIDException(self._device.get_error())
        else:
            assert(ret == 0)
            return ffi.string(str_buf)

    # Probably don't need these excpet for get_indexed_string, since they won't
    # change from the values found in the enumeration
    def get_manufacture_string(self):
        """
        Get the manufacturer string of the device from its device descriptor
        """
        return self._get_prod_string_common(hidapi.hid_get_manufacturer_string)

    def get_product_string(self):
        """
        Get the product string of the device from its device descriptor
        """
        return self._get_prod_string_common(hidapi.hid_get_product_string)

    def get_serial_number(self):
        """
        Get the serial number string of the device from its device descriptor
        """
        return self._get_prod_string_common(hidapi.hid_get_serial_number_string)

    def get_indexed_string(self, index):
        """
        Get the string with the given index from the device
        """
        max_len = 128
        str_buf = ffi.new("wchar_t[]", str(bytearray(max_len)))
        ret = hidapi.hid_get_indexed_string(self._device, index, str_buf, max_len)

        if ret < 0:
            raise HIDException(self._device.get_error())
        elif ret == 0:
            return None
        else:
            return ffi.string(str_buf).encode('utf-8')


    def description(self):
        """
        Get a string describing the HID descriptor.
        """
        return \
"""HIDDevice:
    {} | {:x}:{:x} | {} | {} | {}
    release_number: {}
    usage_page: {}
    usage: {}
    interface_number: {}\
""".format(self.path,
           self.vendor_id,
           self.product_id,
           self.manufacturer_string,
           self.product_string,
           self.serial_number,
           self.release_number,
           self.usage_page,
           self.usage,
           self.interface_number
        )

class Enumeration(object):
    def __init__(self, vid=0, pid=0):
        """
        Create a USB HID enumeration. The enumeration is a list of all the HID
        interfaces connected at the time the object was created.
        """
        self.device_list = _hid_enumerate(vid, pid)

    def show(self):
        """
        Print the device description of each device in the Enumeration
        """
        for dev in self.device_list:
            print(dev.description())

    def find(self, vid=None, pid=None, serial=None, interface=None, \
            path=None, release_number=None, manufacturer=None,
            product=None, usage=None, usage_page=None):
        """
        Attempts to open a device in this `Enumeration` object. Optional
        arguments can be provided to filter the resulting list based on various
        parameters of the HID devices.

        Args:
            vid: filters by USB Vendor ID
            pid: filters by USB Product ID
            serial: filters by USB serial string (.iSerialNumber)
            interface: filters by interface number (bInterfaceNumber)
            release_number: filters by the USB release number (.bcdDevice)
            manufacturer: filters by USB manufacturer string (.iManufacturer)
            product: filters by USB product string (.iProduct)
            usage: filters by HID usage
            usage_page: filters by HID usage_page
            path: filters by HID API path.
        """
        result = []

        for dev in self.device_list:
            if vid not in [0, None] and dev.vendor_id != vid:
                continue
            if pid not in [0, None] and dev.product_id != pid:
                continue
            if serial and dev.serial_number != serial:
                continue
            if path and dev.path != path:
                continue
            if manufacturer and dev.manufacturer_string != manufacturer:
                continue
            if product and dev.product_string != product:
                continue
            if release_number != None and dev.release_number != release_number:
                continue
            if interface != None and dev.interface_number != interface:
                continue
            if usage != None and dev.usage != usage:
                continue
            if usage_page != None and dev.usage_page != usage_page:
                continue
            result.append(dev)
        return result


def _hid_enumerate(vendor_id=0, product_id=0):
    """
    Enumerates all the hid devices for VID:PID. Returns a list of `HIDDevice`
    objects.  If vid is 0, then match any vendor id. Similarly, if pid is 0,
    match any product id. If both are zero, enumerate all HID devices.
    """
    start = hidapi.hid_enumerate(vendor_id, product_id)
    result = []
    cur = ffi.new("struct hid_device_info*");
    cur = start

    # Copy everything into python list
    while cur != ffi.NULL:
        result.append(HIDDevice(cur))
        cur = cur.next

    # Free the C memory
    hidapi.hid_free_enumeration(start)

    return result

# def hid_open(vendor_id, product_id, serial=None):
#     """
#     """
#     if serial == None:
#         serial = ffi.NULL
#     else:
#         if type(serial) == bytes or type(serial) == bytearray:
#             serial = serial.decode('utf-8')
#         serial = ffi.new("wchar_t[]", serial)
#     dev = hidapi.hid_open(vendor_id, product_id, serial)
#     if dev:
#         return HIDDevice(dev)
#     else:
#         None

if __name__ == "__main__":
    # Examples
    from easyhid import Enumeration

    # Stores an enumeration of all the connected USB HID devices
    en = Enumeration()

    # return a list of devices based on the search parameters
    devices = en.find(manufacturer="Company", product="Widget", interface=3)

    # print a description of the devices found
    for dev in devices:
        print(dev.description())

    # open a device
    dev.open()

    # write some bytes to the device
    dev.write(bytearray([0, 1, 2, 3]))

    # read some bytes
    print(dev.read())

    # close a device
    dev.close()
