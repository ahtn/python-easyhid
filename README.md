# easyhid

A simple python interface to the HIDAPI library.

```python
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
```
