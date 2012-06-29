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
        pass

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
    LS_core("ldrex"    False,    32,      Extra.EX,        False ),
    LS_core("strex",   True,     32,      Extra.EX,        False ),
    LS_core("strh",    True,     16,      Extra.NONE,      False ),
    LS_core("strht",   True,     16,      Extra.UNPRIV,    False ),
    LS_core("strexh",  True,     16,      Extra.EX,        False ),
    LS_core("ldrh",    False,    16,      Extra.NONE,      False ),
    LS_core("ldrht",   False,    16,      Extra.UNPRIV,    False ),
    LS_core("ldrexh",  False,    16,      Extra.EX,        False ),
    LS_core("ldrsh",   False,    16,      Extra.NONE,      True  ),
    LS_core("ldrsht",  False,    16,      Extra.UNPRIV,    True  ),
    LS_core("strb",    True,      8,      Extra.NONE,      False ),
    LS_core("strbt",   True,      8,      Extra.UNPRIV,    False ),
    LS_core("strexb",  True,      8,      Extra.EX,        False ),
    LS_core("ldrb",    False,     8,      Extra.NONE,      False ),
    LS_core("ldrbt",   False,     8,      Extra.UNPRIV,    False ),
    LS_core("ldrexb",  False,     8,      Extra.EX,        False ),
    LS_core("ldrsb",   False,     8,      Extra.NONE,      True  ),
    LS_core("ldrsbt",  False,     8,      Extra.UNPRIV,    True  ),
    LS_core("ldrd",    False,    64,      Extra.NONE,      False ),
    LS_core("strd",    True,     64,      Extra.NONE,      False ),
    LS_core("ldrexd",  False,    64,      Extra.NONE,      False ),
    LS_core("strexd",  True,     64,      Extra.NONE,      False ),
    ]


if __name__ == "__main__":
    for inst in LS_core_list:
        print inst.instr
