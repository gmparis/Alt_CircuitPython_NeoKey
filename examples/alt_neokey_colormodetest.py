# SPDX-FileCopyrightText: Copyright (c) 2021 Greg Paris
#
# SPDX-License-Identifier: MIT

# Demonstrate changing auto_color action to produce
# different modes. This example uses key 0 to do it,
# but a real program might change modes based upon
# some measured condition.

import board
from alt_neokey.alt_neokey1x4 import NeoKey1x4

print("Alt API NeoKey color modes test")


def normal_mode(kev):
    return 0xFF0000 if kev.pressed else 0x777777


def special_mode(kev):
    return 0xFF7700 if kev.pressed else 0x007700


i2c = board.I2C()
neokey = NeoKey1x4(i2c, auto_color=normal_mode)

while True:
    for event in neokey.read():
        if event.pressed and event.key_num == 0:
            if neokey.auto_color is normal_mode:
                neokey.auto_color = special_mode
            else:
                neokey.auto_color = normal_mode
