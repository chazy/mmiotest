#!/usr/bin/python

"""generate.py: Generate all possible load-store ARM instructions
   Copyright (C) 2012 Christoffer Dall <cdall@cs.columbia.edu>

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.# 
"""

__author__    = "Christoffer Dall"
__email__     = "cdall@cs.columbia.edu"
__copyright__ = "Copyright 2012, Virtual Open Systems"
__license__   = "GPL"

DATA_SIZE = 4096

class Extra:
    NONE   = 0
    UNPRIV = 1
    EXCL   = 2

class LS_core:
    def __init__(self, instr, store, extra, length, signed):
        self.instr = instr
        self.store = store
        self.extra = extra
        self.length = length
        self.signed = signed

#
# List of core load/store instructions
#
#           Instr    | Store   | Length | Extra          | Signed
#           ----------------------------------------------------
LS_core_list = [
    LS_core("ldr",     False,    32,      Extra.NONE,      False ),
    LS_core("str",     True,     32,      Extra.NONE,      False ),
    LS_core("ldrt",    False,    32,      Extra.UNPRIV,    False ),
    LS_core("strt",    True,     32,      Extra.UNPRIV,    False ),
    LS_core("ldrex",   False,    32,      Extra.EXCL,      False ),
    LS_core("strex",   True,     32,      Extra.EXCL,      False ),
    LS_core("strh",    True,     16,      Extra.NONE,      False ),
    LS_core("strht",   True,     16,      Extra.UNPRIV,    False ),
    LS_core("strexh",  True,     16,      Extra.EXCL,      False ),
    LS_core("ldrh",    False,    16,      Extra.NONE,      False ),
    LS_core("ldrht",   False,    16,      Extra.UNPRIV,    False ),
    LS_core("ldrexh",  False,    16,      Extra.EXCL,      False ),
    LS_core("ldrsh",   False,    16,      Extra.NONE,      True  ),
    LS_core("ldrsht",  False,    16,      Extra.UNPRIV,    True  ),
    LS_core("strb",    True,      8,      Extra.NONE,      False ),
    LS_core("strbt",   True,      8,      Extra.UNPRIV,    False ),
    LS_core("strexb",  True,      8,      Extra.EXCL,      False ),
    LS_core("ldrb",    False,     8,      Extra.NONE,      False ),
    LS_core("ldrbt",   False,     8,      Extra.UNPRIV,    False ),
    LS_core("ldrexb",  False,     8,      Extra.EXCL,      False ),
    LS_core("ldrsb",   False,     8,      Extra.NONE,      True  ),
    LS_core("ldrsbt",  False,     8,      Extra.UNPRIV,    True  ),
    LS_core("ldrd",    False,    64,      Extra.NONE,      False ),
    LS_core("strd",    True,     64,      Extra.NONE,      False ),
    LS_core("ldrexd",  False,    64,      Extra.NONE,      False ),
    LS_core("strexd",  True,     64,      Extra.NONE,      False ),
    ]

#
# The ARM instruction set specifies that load/stores are performed using:
#  - a base register
#  - an offset
#
# For testing we use:
#  - Dest reg:   r0, r3
#  - Base reg:   r2, r5  (preload to start and end)
#  - Offset reg: r8, r11 (preload to 8, 16)
#
# The following combinations show the (mostly) valid combinations:
#
#   mode         |    Immediate      Register        Scaled register
# ---------------|----------------------------------------------------
#  Offset        |   [Rn, #off]      [Rn, Rm]    [Rn, Rm, LSL #shift]
#  Pre-indexed   |   [Rn, #off]!     [Rn, Rm]!   [Rn, Rm, LSL #shift]!
#  Post-indexed  |   [Rn], #off]     [Rn], Rm    [Rn], Rm, LSL #shift
#
# TODO: Additional things to test for
#  - Rm is always both +/-
#  - test RRX shift on scaled register
#

class Addressing:
    def __init__(self, end, offset, data_off):
        self.end = end              # if end, base is end of data
        self.offset = offset
        self.data_off = data_off
        self.addr_spec = ""


def ls_instr_addrs():
    lst = []

    lst.append(  Addressing(0,     "#0",     0)  )
    lst.append(  Addressing(0,    "#13",    13)  )
    lst.append(  Addressing(0,    "#16",    16)  )
    lst.append(  Addressing(0,   "#124",   124)  )
    lst.append(  Addressing(0,   "#255",   255)  )
    lst.append(  Addressing(0,  "#4095",  4095)  )

    lst.append(  Addressing(1,    "#-0",  DATA_SIZE - (1 +   0)  )
    lst.append(  Addressing(1,   "#-13",  DATA_SIZE - (1 +  13)  )
    lst.append(  Addressing(1,   "#-16",  DATA_SIZE - (1 +  16)  )
    lst.append(  Addressing(1,  "#-124",  DATA_SIZE - (1 + 124)  )
    lst.append(  Addressing(1,  "#-255",  DATA_SIZE - (1 + 255)  )
    lst.append(  Addressing(1, "#-4095",  DATA_SIZE - (1 +4095)  )

    lst.append(  Addressing(0, "r8",   8)  )
    lst.append(  Addressing(0, "r11", 16)  )

    lst.append(  Addressing(0,  "r8, LSL #1",   16)  )
    lst.append(  Addressing(0,  "r8, LSL #2",   32)  )
    lst.append(  Addressing(0, "r11, LSR #1",    8)  )

    return lst

# As input, the base register should be simply %1
def generate_ls_test(instr, dst, addr, ls_len):
    if ls_len == 1:
        cast = "char"
    elif ls_len == 2:
        cast = "short"
    elif ls_len == 4:
        cast = "int"
    elif ls_len == 8:
        cast = "long long"

    if not addr.end:
        base = "io_data"
    else:
        base = "(io_data + %d - 1)" % (DATA_SIZE)


    code = """
        asm volatile("%s\n\t"
                     "mov %0, r%d" : "=r"(out) :
                                     "r" (%s));
        assert(out == *(%s *)(io_data + offset));
""" % (instr, dst, base, cast, addr.data_off)
    return code

off_list = ls_instr_offsets()
def ls_instr_vars(instr):
    lst = []
    dst = ["r0", "r3"]
    base = ["r2", "r5"]

    for d in dst:
        for b in base:
            for o in off_list:
                # mode: offset
                i = "%s\t%s, [%s, %s]" %(instr.instr, d, b, o)
                # mode: pre-indexed
                j = "%s\t%s, [%s, %s]!" %(instr.instr, d, b, o)
                # mode: post-indexed
                k = "%s\t%s, [%s], %s" %(instr.instr, d, b, o)
                lst.extend([i, j, k])
    return lst


def generate_ls_instrs():
    lst = []
    code = "\tprint("Perform code load/store tests\\n");\n\n"""
    for i in LS_core_list:

        lst.extend(ls_instr_vars(i))
    return lst



class LDM:
    def __init__(self, instr, store, arm_only, stack):
        self.instr = instr
        self.store = store
        self.arm_only = arm_only
        self.stack = stack
        pass

#
# List of load/store multiple instructions
#
#        Instr    | Store   |  ARM-only | Stack
#        --------------------------------------
LDM_list = [
    LDM("ldmia",    False,     False,     False ),
    LDM("ldmda",    False,     True,      False ),
    LDM("ldmdb",    False,     False,     False ),
    LDM("ldmib",    False,     True,      False ),
    LDM("pop",      False,     False,     True  ),
    LDM("push",     True,      False,     True  ),
    LDM("stmia",    True,      False,     False ),
    LDM("stmda",    True,      True,      False ),
    LDM("stmdb",    True,      False,     False ),
    LDM("stmib",    True,      True,      False ),
    ]

LDM_reglist = []
for first_reg in range(0, 12):
    for n in range(first_reg, 12):
        if LDM_reglist and LDM_reglist[-1][0] == first_reg:
            base_list = list(LDM_reglist[-1])
        else:
            base_list = []
        base_list.append(n)
        LDM_reglist.append(base_list)


if __name__ == "__main__":
    for inst in LS_core_list:
        print inst.instr
    for inst in LDM_list:
        print inst.instr
    for reglist in LDM_reglist:
        print reglist
    print ls_instr_offsets()
    for i in generate_ls_instrs():
        print i

