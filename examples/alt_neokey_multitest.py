# SPDX-FileCopyrightText: Copyright (c) 2021 Greg Paris
#
# SPDX-License-Identifier: MIT

from time import sleep
import gc
import board

print("Alt API NeoKey multi-test")

# report memory before instantiating NeoKey1x4
used1, free1 = gc.mem_alloc(), gc.mem_free()  # pylint: disable=no-member
print(f"Memory: Start: alloc={used1} free={free1}")

from alt_neokey.alt_neokey1x4 import NeoKey1x4  # pylint: disable=wrong-import-position

# optional automatic key color handling
# this time we take advantage of global variables
key_colors = (0x0000FF, 0xFF0000, 0x00FF00, 0xFF6600)
color_index = 0


def my_colors(event):  # pylint: disable=redefined-outer-name
    """Next color each time a key is pressed"""
    global color_index, key_colors  # pylint: disable=global-statement
    if event.pressed:
        color_index = (color_index + 1) % len(key_colors)
        return key_colors[color_index]
    return 0x333333


i2c_bus = board.I2C()

# Create a NeoKey object for two NeoKey1x4 modules
neokey = NeoKey1x4(
    i2c_bus,
    addr=(0x30, 0x31),
    auto_color=my_colors,
)

# report memory again
used2, free2 = gc.mem_alloc(), gc.mem_free()  # pylint: disable=no-member
delta = used2 - used1
print(f"Memory: After: alloc={used2} free={free2} delta={delta}")

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
