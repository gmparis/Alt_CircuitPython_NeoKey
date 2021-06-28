# SPDX-FileCopyrightText: Copyright (c) 2021 Greg Paris
#
# SPDX-License-Identifier: Unlicense

from time import sleep
import board
from alt_neokey.neokey1x4 import NeoKey1x4

print("Alt API NeoKey simple test")

# use default I2C bus
i2c_bus = board.I2C()

# Create a NeoKey object with optional auto_color function
neokey = NeoKey1x4(
    i2c_bus,
    addr=0x30,
    auto_colors=lambda e: 0x00FF33 if e.pressed else 0x000000,
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
