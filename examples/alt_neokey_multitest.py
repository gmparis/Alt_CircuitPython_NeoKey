# SPDX-FileCopyrightText: Copyright (c) 2021 Greg Paris
#
# SPDX-License-Identifier: Unlicense

from time import sleep
import board
from alt_neokey.neokey1x4 import NeoKey1x4

print("Alt API NeoKey multi-test")

# use default I2C bus
i2c_bus = board.I2C()

# optional automatic key color handling
# this time we take advantage of global variables
key_colors = (0x0000FF, 0xFF0000, 0x00FF00, 0xFF6600)
color_index = 0


def my_colors(event):
    """Next color each time a key is pressed"""
    global color_index, key_colors  # pylint: disable=global-statement
    if event.pressed:
        color_index = (color_index + 1) % len(key_colors)
        return key_colors[color_index]
    return 0x333333


# Create a NeoKey object for two NeoKey1x4 modules
neokey = NeoKey1x4(
    i2c_bus,
    addr=(0x30, 0x31),
    auto_colors=my_colors,
)

# Read keys, process any events
# if you want responsive keys, you can't spend much time doing work!
while True:
    events = neokey.read_keys()
    for event in events:
        if event.pressed:
            print(f"key {event.key_num} pressed")
            sleep(0.1)  # pretend to do stuff
        else:
            print(f"key {event.key_num} released")
            sleep(0.1)  # pretend to do stuff
    sleep(0.1)  # pretend to do stuff
