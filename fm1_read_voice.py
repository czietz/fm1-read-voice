#!/usr/bin/env python3

# Read the current voice from M-VAVE FM-1 synthesizer via USB MIDI
# Tested with firmware V14 and V15

# USE AT YOUR OWN RISK!

# Copyright (c) 2026 Christian Zietz
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import sys
import mido
from decode_dx7_voice import print_voice

# Pack data into 7-bit format suitable for SysEx transmission
def pack7(data):
    packed = bytearray()
    buffer = 0
    bits_in_buffer = 0

    for value in data:
        buffer |= value << bits_in_buffer
        bits_in_buffer += 8

        while bits_in_buffer >= 7:
            packed.append(buffer & 0x7F)
            buffer >>= 7
            bits_in_buffer -= 7

    if bits_in_buffer:
        packed.append(buffer & 0x7F)

    return bytes(packed)

# Unpack data from 7-bit format from SysEx transmission
def unpack7(data):
    unpacked = bytearray()
    buffer = 0
    bits_in_buffer = 0

    for value in data:
        buffer |= value << bits_in_buffer
        bits_in_buffer += 7

        while bits_in_buffer >= 8:
            unpacked.append(buffer & 0xFF)
            buffer >>= 8
            bits_in_buffer -= 8

    return bytes(unpacked)

# Make a M-VAVE custom command, give a command byte and a payload
# The length of the payload and the checksum inserted automatically,
# and the command is packed into 7-bit SysEx format
def mkcmd(cmd, payload):
    lp = len(payload)
    cmd = bytearray([0x00,0x59,cmd, lp & 0xff, (lp>>8)&0xff, (lp>>16)&0xff])
    cmd += bytearray(payload)
    cksum = 0
    for x in payload:
        cksum = (cksum + x) & 0xff
    cksum = cksum ^ 0xff
    cmd += bytearray([cksum])
    cmd = pack7(cmd)
    return cmd

# Run the command to dump the current voice from RAM
def voicedump(outport, inport):
    CMD_READ = 0x23
    SUBCMD_VOICE = 5
    VOICE_LEN = 155
                                        # offset  # length
    cmd = mkcmd(CMD_READ, [SUBCMD_VOICE, 0,0,0,0 ,VOICE_LEN,0x00,0x00])
    msg = mido.Message('sysex', data=cmd)
    outport.send(msg)
    msg = inport.receive()
    data = unpack7(msg.data)
    # strip header and checksum
    data = data[0xe:-1]
    return data


if __name__ == "__main__":

    # Find FM-1 MIDI ports
    outport = None
    inport = None

    for p in mido.get_output_names():
        if p.startswith("FM-1"):
            print(f"Using output MIDI port {p}")
            try:
                outport = mido.open_output(p)
            except Exception as e:
                print(e)
                sys.exit(1)
            break
    else:
        print("No FM-1 MIDI output port found")
        sys.exit(1)

    for p in mido.get_input_names():
        if p.startswith("FM-1"):
            print(f"Using input MIDI port {p}")
            try:
                inport = mido.open_input(p)
            except Exception as e:
                print(e)
                sys.exit(1)
            break
    else:
        print("No FM-1 MIDI input port found")
        sys.exit(1)

    # Dump voice
    voice = voicedump(outport, inport)

    # ... and print it to console in human readable format
    print("------------------------")
    print_voice(voice)
