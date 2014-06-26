#!/usr/bin/env python2
"""Trivial CC110L interface via FTDI C232HM-DDHSL-0 cable.

signal pin  FTDI
------ ---- ------
+3.3V  J1.1 RED
clock  J1.7 ORANGE
ground J2.1 BLACK
select J2.3 BROWN
MOSI   J2.6 YELLOW
MISO   J2.7 GREEN

Will generalize and clean up using the bitmask lib + defs later. Goal is to
eventually abstract away:

    - read-then-write vs check-cache-then-write vs use-default-then-write for
      setting bitfields within a register
    - rewriting of sequential reads/writes into bursts as a transparent
      optimization
    - managing of volatile burst-accessible FIFOs and wide config regs
    - FCC/ETSI-compatible register masking when using register settings defined
      by Anaren docs
"""
try:
    from mpsse import MPSSE, SPI0, MSB, ONE_HUNDRED_KHZ
except:
    print """Missing dependency. You need recent versions of:

    libftdi:    http://www.intra2net.com/en/developer/libftdi/
    libmpsse:   https://code.google.com/p/libmpsse/"""
    exit(1)

import time

class Comm(object):
    """Ghetto first iteration on master, manual commands."""
    def __init__(self):
        self.spi = MPSSE(SPI0, ONE_HUNDRED_KHZ, MSB)
        print 'chip', self.spi.GetDescription()
        print 'freq', self.spi.GetClock()

    def strobe(self, addr):
        """Commands with no arguments"""
        assert 0x30 <= addr <= 0x3f # right range +
        return self.txn(chr(addr)) # read flag

    def write(self, addr, val):
        """Single byte writes, status byte overhead"""
        assert 0x00 <= addr <= 0x2f  or addr == 0x3f
        return self.txn(chr(addr) + chr(val))

    def read(self, addr):
        """Single byte reads, status byte overhead"""
        assert 0x00 <= addr <= 0x2f or addr == 0x3f
        return self.txn(chr(addr | 0x80) + '\xff')

    def read_high(self, addr):
        assert 0x30 <= addr <= 0x3f 
        pass # TODO

    def txn(self, payl):
        """Arbitrary send-receives, status byte always parsed."""
        def status(n):
            STATE = '''IDLE RX TX FSTXON CALIBRATE SETTLING 
                       RXFIFO_OVERFLOW TXFIFO_UNDERFLOW'''.split()
            fifo = n & 0x0f
            state = STATE[(n & 0x70) >> 4]
            is_ready = 'NOTready' if n >> 7 else 'ready'
            return (is_ready, state, fifo)
        resp = self.spi.Transfer(payl)
        stat = status(ord(resp[0]))
        return (stat, resp[1:].encode('hex'))


def main():
    dev = Comm()
    dev.spi.Start()

    # burst + read 
    #for c in '\xf0\xf1\xf2\xf3\xf4\xf5\xf8\xfa\xfb': # some stat reg reads
    #    print c.encode('hex')+'->'+spi.Transfer(c + '\xff').encode('hex')

    # !burst + read 
    #for c in '\x86\x87\x88\x89\x8a': # some stat reg reads
    #    print c.encode('hex')+'->'+spi.Transfer(c + '\xff').encode('hex')

    dev.strobe(0x30) # reset
    time.sleep(0.01) # this seems to get it into a stable state

    for n in range(0x30):
        print hex(n), '->', dev.read(n)

    #print 'Writing default config...'
    #import anaren
    #for addr, val in anaren.fcc_default:
    #    dev.write(addr, val)

    print 'Sanity checking...'
    for n in range(0x30):
        print hex(n), '->', dev.read(n)

    dev.strobe(0x35) # enable transmit

    for n in range(10):
        print 'tx fifo write:', dev.write(0x3f, 1)
        print 'tx fifo write:', dev.write(0x3f, 2)
        time.sleep(0.001)

    dev.spi.Stop()


main()
