About
=============

A small test program to create a VM that does all sorts of MMIO
operations and verify that these get decoded properly by the
KVM/ARM module.

License: GPLv3


Usage
=============

In theory:

    git clone git://github.com/chazy/mmiotest.git
    cd mmiotest
    make
    ./guest-driver <mmio-test.o>
