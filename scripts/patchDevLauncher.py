# -*- coding: utf8 -*-
# Patch an .nds (works with homebrew and ds demo only) to make it ready for make_cia
#
# 2016-02-28, Ahezard 
#
# inspired by 
# Apache Thunder .nds edited files and comments
# https://github.com/Relys/Project_CTR/blob/master/makerom/srl.h
# https://dsibrew.org/wiki/DSi_Cartridge_Header
# if the header size of the input nds file is 0x200 (homebrew)
# the header size of the output nds file will be patched to 0x4000 (normal ds/dsi header), 0x3E00 offset

from struct import *
from collections import namedtuple
from collections import OrderedDict
from pprint import pprint
import os, sys
import binascii
import argparse
import mmap


parser = argparse.ArgumentParser(description='extract devLauncherSrl from the twl_bg.cxi')
parser.add_argument('--srl', help='srl file')
parser.add_argument('--out', help='output code file')
args = parser.parse_args()

#
# CRC16 MODULE
#
# includes CRC16 and CRC16 MODBUS
#

from ctypes import c_ushort

# from https://github.com/cristianav/PyCRC/blob/master/demo.py
class CRC16(object):
    crc16_tab = []

    # The CRC's are computed using polynomials. Here is the most used
    # coefficient for CRC16
    crc16_constant = 0xA001  # 40961

    def __init__(self, modbus_flag=False):
        # initialize the precalculated tables
        if not len(self.crc16_tab):
            self.init_crc16()
        self.mdflag = bool(modbus_flag)

    def calculate(self, input_data=None):
        try:
            is_string = isinstance(input_data, str)
            is_bytes = isinstance(input_data, (bytes, bytearray))

            if not is_string and not is_bytes:
                raise Exception("Please provide a string or a byte sequence "
                                "as argument for calculation.")

            crc_value = 0x0000 if not self.mdflag else 0xffff

            for c in input_data:
                d = ord(c) if is_string else c
                tmp = crc_value ^ d
                rotated = crc_value >> 8
                crc_value = rotated ^ self.crc16_tab[(tmp & 0x00ff)]

            return crc_value
        except Exception as e:
            print("EXCEPTION(calculate): {}".format(e))

    def init_crc16(self):
        """The algorithm uses tables with precalculated values"""
        for i in range(0, 256):
            crc = c_ushort(i).value
            for j in range(0, 8):
                if crc & 0x0001:
                    crc = c_ushort(crc >> 1).value ^ self.crc16_constant
                else:
                    crc = c_ushort(crc >> 1).value
            self.crc16_tab.append(crc)

def getSize(fileobject):
	current = fileobject.tell()
	fileobject.seek(0,2) # move the cursor to the end of the file
	size = fileobject.tell()
	fileobject.seek(current,0)
	return size

def skipUntilAddress(f_in,f_out, caddr, taddr):
	chunk = f_in.read(taddr-caddr)
	f_out.write(chunk)

def writeBlankuntilAddress(f_out, caddr, taddr):
	f_out.write("\x00"*(taddr-caddr))

srl_fname=args.srl

# write the file
files = open(srl_fname, 'rb')
filew = open(args.out, "wb")

filesize=getSize(files)

# 1st patch
srlsizeoffset=0xAC535
skipUntilAddress(files,filew,0,srlsizeoffset)
files.read(1)
filew.write("\x00")
current=srlsizeoffset+1

# 2nd patch
srlsizeoffset=0xAC589
skipUntilAddress(files,filew,current,srlsizeoffset)
files.read(1)
filew.write("\x00")
current=srlsizeoffset+1

# 3rd patch
srlsizeoffset=0xAC58C
skipUntilAddress(files,filew,current,srlsizeoffset)
files.read(5)
filew.write("\x73\x64\x6D\x63\x00")
current=srlsizeoffset+5

# 4th patch
srlsizeoffset=0xAC5DD
skipUntilAddress(files,filew,current,srlsizeoffset)
files.read(1)
filew.write("\x10")
current=srlsizeoffset+1

# 5th patch
srlsizeoffset=0xAC631
skipUntilAddress(files,filew,current,srlsizeoffset)
files.read(1)
filew.write("\x10")
current=srlsizeoffset+1

# 6th patch
srlsizeoffset=0xAC685
skipUntilAddress(files,filew,current,srlsizeoffset)
files.read(1)
filew.write("\x10")
current=srlsizeoffset+1

# 7th patch
srlsizeoffset=0xAC6D9
skipUntilAddress(files,filew,current,srlsizeoffset)
files.read(1)
filew.write("\x10")
current=srlsizeoffset+1

# 8th patch
srlsizeoffset=0xAC6EC
skipUntilAddress(files,filew,current,srlsizeoffset)
files.read(12)
filew.write("\x73\x64\x6D\x63\x3A\x2F\x70\x68\x6F\x74\x6F\x00")
current=srlsizeoffset+12

# 9th patch
srlsizeoffset=0xAC72D
skipUntilAddress(files,filew,current,srlsizeoffset)
files.read(1)
filew.write("\x08")
current=srlsizeoffset+1

skipUntilAddress(files,filew,0,filesize)

filew.close()
files.close()

