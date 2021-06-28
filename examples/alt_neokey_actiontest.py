# SPDX-FileCopyrightText: Copyright (c) 2021 Greg Paris
#
# SPDX-License-Identifier: Unlicense

from time import sleep
import board
from alt_neokey.neokey1x4 import NeoKey1x4

print("Alternative API NeoKey action test")

# use default I2C bus
i2c_bus = board.I2C()


# optional automatic key color handling
# this time we give each key a different pressed color
key_colors = (
    0x0000FF,
    0xFF0000,
    0x00FF00,
    0xFF7700,
    0x7700FF,
    0xFF0077,
    0x00FF77,
    0xFFFFFF,
)


def my_colors(event):
    return key_colors[event.key_num] if event.pressed else 0


# this time, instead of reading the event list, we'll perform an automatic action
def my_action(event):
    if event.pressed:
        print(f"key {event.key_num} pressed")
    else:
        print(f"key {event.key_num} released")
    sleep(0.1)  # pretend to do stuff


# Create a NeoKey object for two NeoKey1x4 modules
neokey = NeoKey1x4(
    i2c_bus,
    addr=(0x30, 0x31),
    auto_colors=my_colors,
    auto_action=my_action,
)

# Read keys, process any events
# if you want responsive keys, you can't spend much time doing work!
while True:
    events = neokey.read_keys()
    sleep(0.1)  # pretend to do stuff
