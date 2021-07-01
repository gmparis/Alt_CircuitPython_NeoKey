# SPDX-FileCopyrightText: Copyright (c) 2021 Greg Paris
#
# SPDX-License-Identifier: Unlicense

from random import randrange
from collections import namedtuple
import board
from alt_neokey.neokey1x4 import NeoKey1x4

# If you have one module, swap which line is commented.
# MODULES = 0x30
MODULES = (0x30, 0x31)

# This example is more fun than the rest!
print("Alternative API NeoKey blink test")

# use default I2C bus
i2c_bus = board.I2C()

System = namedtuple("System", "name color")
SYSTEMS = (
    System("AM CONTAIMENT", 0x0000FF),
    System("WARP COILS", 0xFF0000),
    System("SUBSPACE COMMS", 0x00FF00),
    System("TRANSPORTER", 0xFF7700),
    System("DECOM CHAMBER", 0x7700FF),
    System("MED BAY", 0xFF0077),
    System("HULL PLATING", 0x00FF77),
    System("PHASE CANNONS", 0xFFFFFF),
)


def my_colors(event):
    # blink will default to white if the released color is 0
    # so, this time, we'll choose to go dark when pressed.
    # Other than the weird colors for this demo, this looks great!
    return 0 if event.pressed else SYSTEMS[event.key_num].color


# Create a NeoKey object for two NeoKey1x4 modules
neokey = NeoKey1x4(
    i2c_bus,
    addr=MODULES,
    auto_colors=my_colors,
    blink=False,  # use blink selectively (default)
)

# This time, our automatic action will be to change whether
# the key is blinking. We may do it on pressed or released,
# but not both, since that would negate itself. Also, we
# must define this function *after* we have neokey, since
# we need a reference to it.
def my_action(event):
    if event.pressed:
        key = neokey[event.key_num]  # this is a NeoKey_Key object
        key.blink = not key.blink
        if key.blink:
            print(f"ALERT on {SYSTEMS[event.key_num].name}!")
        else:
            print(f"{SYSTEMS[event.key_num].name} alert cleared.")


neokey.set_auto_action(my_action)

# We have some warnings!
for _ in range(3):
    key_num = randrange(len(neokey))
    neokey[key_num].blink = True

# Read keys, process any events. Manage colors and blinking.
# If you want responsive keys, you can't spend much time doing work!
# All of the simulated work sleeps have been removed in this example
# to demonstrate the best-case performance.
while True:
    neokey.read_keys()