# SPDX-FileCopyrightText: Copyright (c) 2021 Greg Paris
#
# SPDX-License-Identifier: MIT

# A fanciful example that shows two NeoKey 1x4 keypads
# being used to alert on the status of critical ship
# systems. Because the auto_action function needs to
# reference the NeoKey1x4 instance, the function is
# defined after the constructor and put into effect
# using the auto_action property.

from collections import namedtuple
from random import randrange
import gc
import board

print("Alternative API NeoKey blink test")

# report memory before instantiating NeoKey1x4
used1, free1 = gc.mem_alloc(), gc.mem_free()  # pylint: disable=no-member
print(f"Memory: Start: alloc={used1} free={free1}")

from alt_neokey.alt_neokey1x4 import NeoKey1x4  # pylint: disable=wrong-import-position

# If you have one module, swap which line is commented.
# MODULES = 0x30
MODULES = (0x30, 0x31)

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


def my_colors(kev):
    # blink will default to white if the released color is 0
    # so, this time, we'll choose to go dark when pressed.
    # Other than the weird colors for this demo, this looks great!
    return 0 if kev.pressed else SYSTEMS[kev.key_num].color


i2c_bus = board.I2C()

# Create a NeoKey object for two NeoKey1x4 modules
neokey = NeoKey1x4(
    i2c_bus,
    addr=MODULES,
    auto_color=my_colors,
    blink=False,  # use blink selectively (default)
)

# This time, our automatic action will be to change whether
# the key is blinking. We may do it on pressed or released,
# but not both, since that would negate itself. Also, we
# must define this function *after* we have neokey, since
# we need a reference to it.
def my_action(kev):
    if kev.pressed:
        key = neokey[kev.key_num]  # this is a NeoKey_Key object
        key.blink = not key.blink
        if key.blink:
            print(f"ALERT on {SYSTEMS[kev.key_num].name}!")
        else:
            print(f"{SYSTEMS[kev.key_num].name} alert cleared.")


neokey.auto_action = my_action

# We have some warnings!
for _ in range(3):
    key_num = randrange(len(neokey))
    neokey[key_num].blink = True

# report memory again
used2, free2 = gc.mem_alloc(), gc.mem_free()  # pylint: disable=no-member
delta = used2 - used1
print(f"Memory: After: alloc={used2} free={free2} delta={delta}")

# Read keys, process any events. Manage colors and blinking.
# If you want responsive keys, you can't spend much time doing work!
# All of the simulated work sleeps have been removed in this example
# to demonstrate the best-case performance.
while True:
    neokey.read()
