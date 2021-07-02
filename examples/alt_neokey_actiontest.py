# SPDX-FileCopyrightText: Copyright (c) 2021 Greg Paris
#
# SPDX-License-Identifier: MIT

from time import sleep
import gc
import board

print("Alternative API NeoKey action test")

# report memory before instantiating NeoKey1x4
used1, free1 = gc.mem_alloc(), gc.mem_free()  # pylint: disable=no-member
print(f"Memory: Start: alloc={used1} free={free1}")

from alt_neokey.alt_neokey1x4 import NeoKey1x4  # pylint: disable=wrong-import-position

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


i2c_bus = board.I2C()

# Create a NeoKey object for two NeoKey1x4 modules
neokey = NeoKey1x4(
    i2c_bus,
    addr=(0x30, 0x31),
    auto_colors=my_colors,
    auto_action=my_action,
)

# report memory again
used2, free2 = gc.mem_alloc(), gc.mem_free()  # pylint: disable=no-member
delta = used2 - used1
print(f"Memory: After: alloc={used2} free={free2} delta={delta}")

# Read keys, process any events
# if you want responsive keys, you can't spend much time doing work!
while True:
    events = neokey.read_keys()
    sleep(0.1)  # pretend to do stuff
