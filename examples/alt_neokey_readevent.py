# SPDX-FileCopyrightText: Copyright (c) 2021 Greg Paris
#
# SPDX-License-Identifier: MIT

# This is the same example as blinktest, but uses
# the read_event() method. Jump to the bottom to see.
#
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

print("Alternative API NeoKey read event test")

# report memory before instantiating NeoKey1x4
used1, free1 = gc.mem_alloc(), gc.mem_free()  # pylint: disable=no-member
print(f"Memory: Start: alloc={used1} free={free1}")

from alt_neokey.alt_neokey1x4 import NeoKey1x4  # pylint: disable=wrong-import-position

System = namedtuple("System", ("name", "color"))
SYSTEMS = (
    System("AM CONTAIMENT", 0x0000FF),
    System("WARP COILS", 0xFF0000),
    System("SUBSPACE COMMS", 0x00FF00),
    System("TRANSPORTER", 0xFF7700),
    System("DECOM CHAMBER", 0x7700FF),
    System("MED BAY", 0xFF0077),
    System("HULL PLATING", 0x00FF77),
    System("PHASE CANNONS", 0xFF00FF),
)


def my_colors(kev):
    # blink will default to white if the released color is 0
    # so, this time, we'll choose to go dark when pressed.
    # Other than the weird colors for this demo, this looks great!
    # Just in case you have more than two modules connected,
    # defaults to white.
    if kev.pressed:
        return 0
    try:
        return SYSTEMS[kev.key_num].color
    except IndexError:
        return 0xFFFFFF


i2c_bus = board.I2C()

# Create a NeoKey object for all NeoKey1x4 modules
# on the i2c buss using the class method all().
neokey = NeoKey1x4.all(
    i2c_bus,
    auto_color=my_colors,
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
        try:
            system = SYSTEMS[kev.key_num].name
        except IndexError:
            system = f"#{kev.key_num}"
        if key.blink:
            print(f"ALERT on {system}!")
        else:
            print(f"{system} alert cleared.")


neokey.auto_action = my_action

# We have some warnings!
for _ in range(3):
    key_num = randrange(len(neokey))
    neokey[key_num].blink = True

# report memory again
used2, free2 = gc.mem_alloc(), gc.mem_free()  # pylint: disable=no-member
delta = used2 - used1
print(f"Memory: After: alloc={used2} free={free2} delta={delta}")

# With read_event(), we no longer need a "while True:".
# But, by default, read_event() doesn't return without an event,
# so no processing can happen unless a key is pressed or
# released. Depending on your application, this is either
# perfectly fine or is a critical flaw.
#
# To overcome this issue, specify a timeout in 10ths of a
# second, as done below. This will cause read_event() to
# return None after the specified number of second tenths
# has elapsed with no key presses or releases. The timeout
# in this example is one second.
for event in neokey.read_event(timeout=10):
    if event is None:
        print("got timeout")
    else:
        print(event)
