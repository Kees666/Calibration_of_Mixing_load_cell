# -*- coding: utf-8 -*-
"""
Created on Fri Mar 26 16:02:49 2021

@author: kjl
"""
# pylint: disable=invalid-name
# %%
import os
import sys
import ctypes
from ctypes import CDLL, c_bool, c_ubyte, c_int, c_uint, c_ulong, c_double, byref, c_void_p
import _ctypes
import time
from threading import Thread, Lock
import datetime
import feather

# Load the switchedgator library
# path = r"C:\Users\KJL\Desktop\Experimenten en analyse\Compass\Gator_software\Python\switchedgator_API_windows_v1.6\64-bit\switchedgator.dll"
# For determine 32 or 64-bit Python
location_dll_64 = os.path
if sys.maxsize > 3 ** 32:
    lib = CDLL('./64-bit/basicgator.dll')
else:
    lib = CDLL('./32-bit/basicgator.dll')

libHandle = lib._handle

# Connect to a Switchedgator is attached
BG_connect = lib['connect_BG']
# Reset the connection
BG_reset = lib['reset']
# Read data of a defined length from the attached Switchedgator. The data includes:
BG_read = lib['BG_read']
# Close connection
BG_closePort = lib['closePort']
# Purger data buffer in the Switchedgator
BG_purgeBuffer = lib['purgeBuffer']
# Get full-scale range
BG_getFullScaleRange = lib['getFullScaleRange']
# Get threshold for CoG algorithm
BG_getThreshold = lib['getThreshold']
# Set full-scale range
BG_setFullScaleRange = lib['setFullScaleRange']
# Set threshold for CoG algorithm
BG_setThreshold = lib['setThreshold']
# Start sensor data stream
BG_startDataStream = lib['startDataStream']
# Stop sensor data stream
BG_stopDataStream = lib['stopDataStream']
# Read sensor data stream
BG_readDataStream = lib['readDataStream']
# Get photodiode signal levels
BG_getPhotodiodeSignalLevels = lib['getPhotodiodeSignalLevels']
# Auto calibration FSR
BG_autoCalibrationFSR = lib['autoCalibrationFSR']
# Get the library version
BG_version = lib['version']

# Define return types
BG_connect.restype = c_int
BG_reset.restype = c_int
BG_read.restype = c_int
BG_closePort.restype = c_int
BG_purgeBuffer.restype = c_int
BG_getFullScaleRange.restype = c_ubyte
BG_getThreshold.restype = c_int
BG_setFullScaleRange.restype = c_int
BG_setThreshold.restype = c_int
BG_startDataStream.restype = c_int
BG_stopDataStream.restype = c_int
BG_readDataStream.restype = c_int
BG_getPhotodiodeSignalLevels.restype = c_int
BG_autoCalibrationFSR.restype = c_int
BG_version.restype = c_int

# Define Switched Gator handle
BG_HANDLE = c_void_p()

# %%
# Open communication
returnValue = BG_connect(byref(BG_HANDLE))

# info to save data to.
# Path_directory = r"C:\Users\KJL\Desktop\Liquidz\02_Compass\01_Experimenten\01_Measurements\Random_tests"
# time = datetime.datetime.now()
# # x.strftime("%d%b%YT%H%M%S.%f")
# File_name = "Testfile"+time.strftime("%d%b%YT%H%M%S")+".csv"
# File_path = os.path.join(Path_directory,File_name)

# Purge old data in the USB buffer
returnValue = BG_purgeBuffer(BG_HANDLE)

# Define output format (1: wavelength; 0: CoG bit)
isOutputWavelength = 1

# Define how many sets of sensor data to be read (1 ~ 65535)
dataLength = 10  # Value used for averaging, here is takes average value of 10ms, sampling rate is now 1000ms
dataOut = ((c_uint * 14) * dataLength)()
data_row = []
Raw_data = []
sum_list = []

# %%
loop_alive = Lock()
loop_alive.acquire(blocking=False)


# %%
def get_data():
    is_first_read = True
    sum_list = [[], [], [], [], [], [], [], []]
    while loop_alive.locked():
        try:
            BG_read(BG_HANDLE, byref(dataOut), c_int(dataLength), c_bool(isOutputWavelength))
            # Discard the first read sample set
            if is_first_read:
                is_first_read = False
                continue

            # data_row.append(time)
            data_row = dataOut[0][0:6]

            for i in range(0, dataLength):  # from 0 till 10, in this case.
                for j in range(8):  # 8 sensors
                    sum_list[j].append(
                        dataOut[i][6 + j])  # so adds the sensor output for each 0.1ms, so adds 10 rows of 8 columns

            # Average over dataLength
            for j in range(8):
                data_row.append(
                    sum(sum_list[j]) / dataLength)  # here it sums the rows and devides by dataLength, so takes average
                sum_list[j].clear()  # clears sum_list for next measurement

            time_string = datetime.datetime.now()
            time_string = time_string.strftime("%Y-%m-%dT%H:%M:%S.%f")[0:-3] + "Z"

            data_row.append(time_string)
            Raw_data.append(data_row)
            # Raw_data.append(time)
            # print(data_row)
            # print(time)

        except KeyboardInterrupt:
            time.sleep(2)
            break
    print("Stop measurement")


proc = Thread(target=get_data, daemon=True)
proc.start()

# while True:
#     try:
#         print("in second loop")
#         # print("printing sum list",sum_list)
#         # print(dataOut[-1][0:14])
#         time.sleep(0.5)
#     except KeyboardInterrupt:
#             time.sleep(2)
#             break

# %%
import numpy as np
import pandas as pd


def print_data():
    while True:

        while len(Raw_data) < 1:
            print(len(Raw_data))
            time.sleep(0.1)

        try:
            time.sleep(1)
            print(Raw_data[len(Raw_data) - 1])

        except KeyboardInterrupt:
            print(" ")
            print("stop printing of data")
            loop_alive.release()
            time.sleep(1)
            returnValue = BG_closePort(byref(BG_HANDLE))
            time.sleep(1)
            print("Close port: ", returnValue)

            Header = ["Gator_Timestamp", "Seqnr", "Sync_status", "TEC_status", "Channel_nr", "Sensor_nr",
                      "Wavelength_1", "Wavelength_2", "Wavelength_3", "Wavelength_4", "Wavelength_5", "Wavelength_6",
                      "Wavelength_7", "Wavelength_8", "Time_stamp"]

            time_name = datetime.datetime.now()
            time_name = time_name.strftime("%Y-%m-%dT%H_%M_%S")
            # time_name = time.strftime("%d%b%YT%H%M")

            # Path_save = r"C:\Users\kjl\OneDrive - Jongia NV\Bureaublad\Liquidz_home\02_Compass\01_Experimenten\01_Measurements\02_Measurments_feather\13-09-2021_Calibration"
            Path_save = r"C:\Users\kjl\OneDrive - Jongia NV\Bureaublad\Calibration_testing\Torque"

            if not os.path.exists(Path_save):
                print("folder did not exist")
                os.makedirs(Path_save)
            else:
                print("Folder exists")
            Name_measurement = time_name + "__" +"short__50Nm"

            df = pd.DataFrame(Raw_data, columns=Header)
            Time_stamp = df.pop("Time_stamp")
            df.insert(0, "Time_stamp", Time_stamp)

            file_path = os.path.join(Path_save, Name_measurement)
            df.to_feather(file_path)
            break


print_data()
