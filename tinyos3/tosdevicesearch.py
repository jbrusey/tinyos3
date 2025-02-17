import os
import os.path
import platform

# We search for devices like:
# /sys/bus/usb/devices/2-1.2:1.0/ttyUSB0 (ftdi, cp2102)
# /sys/bus/usb/devices/1-1.2:1.0/tty/ttyACM0 (mcp2200, pic usb firmware)
def getSerialDevs():
    devs = []
    basedir = "/sys/bus/usb/devices"
    for devdir in os.listdir(basedir):  # all usb devs
        if ":" in devdir:  # except hubs
            for filename in os.listdir(basedir + "/" + devdir):
                if filename.startswith("tty"):  # which have uart
                    fileabsname = (
                        basedir + "/" + devdir + "/" + filename
                    )  # at this point, we found all ftdi and cp2102 devices
                    while not fileabsname[
                        -1
                    ].isdigit():  # if it's a directory of uarts, go deeper (ACM devices)
                        for subname in os.listdir(fileabsname):
                            if subname.startswith("tty"):
                                fileabsname += "/" + subname
                                # If we found a tty/ttyACM0, we don't cart about /tty/ttyACM1. This might be a problem,
                                # but probably not (every usb/uart bridge I've seen used separated interfaces for their uarts)
                                break
                    devs.append(fileabsname)
    return devs


def readToVar(path):
    if os.path.isfile(path):
        file = open(path, "r")
        variable = file.read()
        file.close()
        if variable[-1] == "\n":
            variable = variable[:-1]
        return variable
    else:
        return ""


def getDevProperties(portpath):
    properties = {
        "vid": "0",
        "pid": "0",
        "serialnum": "0",
        "location": "0",
        "port": "0",
        "manufacturer": "0",
        "description": "0",
        "active": False,
    }
    usbdevice = portpath.split(":")[0]
    properties["port"] = "/dev/" + portpath.split("/")[-1]
    properties["vid"] = readToVar(usbdevice + "/idVendor")
    properties["pid"] = readToVar(usbdevice + "/idProduct")
    properties["serialnum"] = readToVar(usbdevice + "/serial")
    properties["manufacturer"] = readToVar(usbdevice + "/manufacturer")
    properties["description"] = readToVar(usbdevice + "/product")
    properties["location"] = (
        readToVar(usbdevice + "/busnum") + ":" + readToVar(usbdevice + "/devnum")
    )
    properties["active"] = True
    return properties


def getAllDevices():
    alldevs = []
    for device in getSerialDevs():
        alldevs.append(getDevProperties(device))
    return alldevs
