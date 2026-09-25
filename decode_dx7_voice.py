#!/usr/bin/env python3
"""Decode a Yamaha DX7 155-byte single-voice dump.
"""

# Copyright (c) 2026 Christian Zietz
# Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
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


from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


VOICE_LENGTH = 155
OPERATOR_LENGTH = 21
OPERATOR_COUNT = 6
OPERATOR_NAMES = ("OP1", "OP2", "OP3", "OP4", "OP5", "OP6")
CURVES = ("-LIN", "-EXP", "+EXP", "+LIN")
LFO_WAVES = ("TRIANGLE", "SAW DOWN", "SAW UP", "SQUARE", "SINE", "SAMPLE&HOLD")

def format_values(values: list[int]) -> str:
    return ", ".join(str(value) for value in values)


def decode_operator(data: list[int], operator_number: int) -> dict[str, object]:
    offset = (6 - operator_number) * OPERATOR_LENGTH
    block = data[offset : offset + OPERATOR_LENGTH]

    return {
        "number": operator_number,
        "eg_rates": block[0:4],
        "eg_levels": block[4:8],
        "breakpoint": block[8],
        "left_depth": block[9],
        "right_depth": block[10],
        "left_curve": CURVES[block[11] & 0x03],
        "right_curve": CURVES[block[12] & 0x03],
        "rate_scaling": block[13],
        "amp_mod_sensitivity": block[14],
        "key_velocity_sensitivity": block[15],
        "output_level": block[16],
        "mode": "fixed" if block[17] else "ratio",
        "coarse": block[18],
        "fine": block[19],
        "detune_raw": block[20],
        "detune": block[20] - 7,
    }


def print_operator(operator: dict[str, object]) -> None:
    print(f"  {OPERATOR_NAMES[int(operator['number']) - 1]}:")
    print(f"    EG rates:                 {format_values(operator['eg_rates'])}")
    print(f"    EG levels:                {format_values(operator['eg_levels'])}")
    print(f"    Keyboard breakpoint:      {operator['breakpoint']}")
    print(f"    Keyboard left depth:      {operator['left_depth']}")
    print(f"    Keyboard right depth:     {operator['right_depth']}")
    print(f"    Keyboard left curve:      {operator['left_curve']}")
    print(f"    Keyboard right curve:     {operator['right_curve']}")
    print(f"    Keyboard rate scaling:    {operator['rate_scaling']}")
    print(f"    Amplitude mod sensitivity: {operator['amp_mod_sensitivity']}")
    print(f"    Key velocity sensitivity: {operator['key_velocity_sensitivity']}")
    print(f"    Output level:             {operator['output_level']}")
    print(f"    Oscillator mode:          {operator['mode']}")
    print(f"    Frequency coarse:         {operator['coarse']}")
    print(f"    Frequency fine:           {operator['fine']}")
    print(f"    Detune:                   {operator['detune']}")


def print_voice(data: list[int]) -> None:
    common = data[126:145]
    name_bytes = data[145:155]
    name = bytes(name_bytes).decode("ascii", errors="replace").rstrip()

    print(f"Voice name: {name!r}")
    print(f"Algorithm: {common[8] + 1}")
    print(f"Feedback: {common[9] & 0x07}")
    print(f"Oscillator sync: {'on' if common[10] else 'off'}")
    print(f"Pitch EG rates: {format_values(common[0:4])}")
    print(f"Pitch EG levels: {format_values(common[4:8])}")
    print(f"LFO speed: {common[11]}")
    print(f"LFO delay: {common[12]}")
    print(f"LFO pitch modulation depth: {common[13]}")
    print(f"LFO amplitude modulation depth: {common[14]}")
    print(f"LFO sync: {'on' if common[15] else 'off'}")
    waveform_number = common[16]
    waveform = (
        LFO_WAVES[waveform_number]
        if waveform_number < len(LFO_WAVES)
        else "unknown"
    )
    print(f"LFO waveform: {waveform}")
    print(f"Pitch modulation sensitivity: {common[17]}")
    print(f"Transpose: {common[18]}")
    print()
    print("Operators:")
    for operator_number in range(1, OPERATOR_COUNT + 1):
        print_operator(decode_operator(data, operator_number))


