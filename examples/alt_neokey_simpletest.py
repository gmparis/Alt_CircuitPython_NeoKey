# SPDX-FileCopyrightText: Copyright (c) 2021 Greg Paris
#
# SPDX-License-Identifier: MIT

# Basic test of a single NeoKey 1x4 board. Some sleeps
# are in the demo to give a feel for real work being done.
# The more work your program does, the slower the keys
# will be to respond. Fortunately, this board uses I2C,
# so it will be easy to interface with a faster processor
# if you need to.

from time import sleep
import gc
import board

print("Alt API NeoKey simple test")

# report memory before instantiating NeoKey1x4
used1, free1 = gc.mem_alloc(), gc.mem_free()  # pylint: disable=no-member
print(f"Memory: Start: alloc={used1} free={free1}")

from alt_neokey.alt_neokey1x4 import NeoKey1x4  # pylint: disable=wrong-import-position

i2c_bus = board.I2C()

# Create a NeoKey object with optional auto_color function
neokey = NeoKey1x4(
    i2c_bus,
    addr=0x30,
    auto_color=lambda e: 0x00FF33 if e.pressed else 0x000000,
)

# report memory again
used2, free2 = gc.mem_alloc(), gc.mem_free()  # pylint: disable=no-member
delta = used2 - used1
print(f"Memory: After: alloc={used2} free={free2} delta={delta}")

# Read keys, process any events
# if you want responsive keys, you can't spend much time doing work!
while True:
    events = neokey.read()
    for event in events:
        if event.pressed:
            print(f"key {event.key_num} pressed")
            sleep(0.1)  # pretend to do stuff
        else:
            print(f"key {event.key_num} released")
            sleep(0.1)  # pretend to do stuff
    sleep(0.1)  # pretend to do stuff
