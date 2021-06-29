# SPDX-FileCopyrightText: Copyright (c) 2021 Greg Paris
#
# SPDX-License-Identifier: MIT
"""
`alt_neokey`
================================================================================

Alternative CircuitPython API for NeoKey I2C Keypad


* Author(s): Greg Paris

Implementation Notes
--------------------

**Hardware:**

* `NeoKey 1x4 QT I2C <https://www.adafruit.com/product/4980>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""

# imports

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/gmparis/Alt_CircuitPython_NeoKey.git"

from collections import namedtuple
from micropython import const
from adafruit_seesaw.seesaw import Seesaw
from adafruit_seesaw.neopixel import NeoPixel, GRB

_NEOKEY1X4_BASE_ADDR = const(0x30)
_NEOKEY1X4_LAST_ADDR = const(_NEOKEY1X4_BASE_ADDR | 0x0F)  # 4 addr bridges

_NEOKEY1X4_NEOPIXEL = const(3)
_NEOKEY1X4_KEY0 = const(1 << 4)
_NEOKEY1X4_KEY1 = const(1 << 5)
_NEOKEY1X4_KEY2 = const(1 << 6)
_NEOKEY1X4_KEY3 = const(1 << 7)
_NEOKEY1X4_KEYMASK = const(
    _NEOKEY1X4_KEY0 | _NEOKEY1X4_KEY1 | _NEOKEY1X4_KEY2 | _NEOKEY1X4_KEY3
)
_NEOKEY1X4_KEYS = (_NEOKEY1X4_KEY0, _NEOKEY1X4_KEY1, _NEOKEY1X4_KEY2, _NEOKEY1X4_KEY3)
_NEOKEY1X4_COUNT = const(4)

NeoKeyEvent = namedtuple("NeoKeyEvent", "key_num pressed")
"""Event list element.

    :param int key_num: Key number. 0-3 on first NeoKey1x4, 4-7 on second, etc.
    :param bool pressed: True for key press event; False for key release event."""

# pylint: disable=missing-docstring


class NeoKey_Key:
    """A single key+pixel pairing. One instance is created by NeoKey1x4
    for each key. Keys are numbered 0-3 on the first NeoKey1x4. 4-7 on the second, etc.

    :param ~Seesaw.seesaw seesaw: NeoKey1x4 Seesaw
    :param ~Seesaw.neopixel pixel: NeoKey1x4 NeoPixel
    :param int key_num: key number assigned by NeoKey1x4"""

    __slots__ = ("_seesaw", "_pixel", "_key_num")

    def __init__(self, seesaw, pixel, key_num):
        self._seesaw = seesaw
        self._pixel = pixel
        self._key_num = key_num

    @property
    def pressed(self):
        """Immediate read of this key's state via the I2C bus.
        Returns True if the key is being pressed.
        Has no effect on auto_color or auto_action status."""
        key_bits = self._seesaw.digital_read_bulk(_NEOKEY1X4_KEYMASK)
        key_bits ^= _NEOKEY1X4_KEYMASK  # invert
        return (key_bits & _NEOKEY1X4_KEYS[self._key_num]) != 0

    @property
    def color(self):
        """Key's pixel color. Reads and writes are done over the I2C bus."""
        return self._pixel[self._key_num]

    @color.setter
    def color(self, color):
        self._pixel[self._key_num] = color


def _bits_to_keys(seesaw_num, bits):
    offset = seesaw_num * _NEOKEY1X4_COUNT
    return [(k + offset) for k in range(_NEOKEY1X4_COUNT) if _NEOKEY1X4_KEYS[k] & bits]


class NeoKey1x4:
    """Alternative API for Adafruit's I2C keyboard with NeoPixel lights.

    :param ~busio.I2C i2c_bus: Bus the NeoKey1x4 is connected to
    :param int addr: I2C address (or list of addresses) of NeoKey1x4 module(s)
    :param float brightness: NeoPixel intensity
    :param function auto_colors: set colors when keys pressed/released
    :param function auto_action: run when keys pressed/released

    Basic usage is one NeoKey1x4 module. In that case, supply its I2C address
    as the addr argument.

    To use more than one module at once, instead supply a list (or tuple) of
    I2C addresses as the addr argument. Up to eight modules can be supported
    by solder-bridging the address selectors to give each board a unique
    address. Key numbers will be assigned to the keys in the order of board
    addresses in the list, first 0-3, second 4-7, ..., eighth 28-31.

    To dynamically manipulate key colors without coding it into your main
    loop, create a function that returns a color (24-bit RGB) and pass it
    to the NeoKey1x4 constructor using the auto_colors parameter. The function
    will be called for each key press and key release event, as detected by
    the read_keys method. That method will call the function with a single
    argument, a NeoKeyEvent.

    Similarly, to have read_keys run arbitrary code whenever a key is pressed,
    use the NeoKey14 constructor's auto_action parameter. Any return value
    from the function will be ignored. As with auto_color, it will be passed
    a single NeoKeyEvent argument.

    Any time spent doing anything other than reading keys can detract from
    the responsiveness of the keys. It's probably a good idea to have keys
    change color when they are pressed, so that the user gets immediate
    feedback that the key press has been registered.

    The following example code has the keys light white when pressed.

    .. sourcecode:: python

        import board
        from alt_neokey.neokey1x4 import NeoKey1x4
        i2c = board.I2C()
        neokey = NeoKey14(
            i2c,
            auto_colors=lambda e: 0xFFFFFF if e.pressed else 0
        )
        while True:
            neokey.read_keys()"""

    def __init__(
        self,
        i2c_bus,
        addr=_NEOKEY1X4_BASE_ADDR,
        *,
        brightness=0.2,
        auto_colors=None,
        auto_action=None,
    ):
        try:
            if len(set(addr)) < len(addr):
                raise RuntimeError("duplicates in I2C address list")
        except TypeError:
            addr = (addr,)
        seesaws = []
        pixels = []
        keys = []
        for i2c_addr in addr:
            if (
                not isinstance(i2c_addr, int)
                or i2c_addr < _NEOKEY1X4_BASE_ADDR
                or i2c_addr > _NEOKEY1X4_LAST_ADDR
            ):
                raise RuntimeError(f"'{i2c_addr}' is not a valid I2C address")
            # supplied order of i2c addresses determines offsets
            ss_mod = Seesaw(i2c_bus, i2c_addr)
            seesaws.append(ss_mod)
            ss_mod.pin_mode_bulk(_NEOKEY1X4_KEYMASK, Seesaw.INPUT_PULLUP)
            ss_mod.set_GPIO_interrupts(_NEOKEY1X4_KEYMASK, True)
            np_mod = NeoPixel(
                ss_mod,
                _NEOKEY1X4_NEOPIXEL,
                _NEOKEY1X4_COUNT,
                pixel_order=GRB,
                auto_write=True,
                brightness=brightness,
            )
            pixels.append(np_mod)
            np_mod.fill(0)
            for key_num, _ in enumerate(_NEOKEY1X4_KEYS):
                keys.append(NeoKey_Key(ss_mod, np_mod, key_num))
        self._seesaws = tuple(seesaws)
        self._pixels = tuple(pixels)
        self._keys = tuple(keys)
        self._brightness = brightness
        self._key_bits = [0x0] * len(seesaws)
        self._set_auto_colors(auto_colors)
        self._set_auto_action(auto_action)

    def __getitem__(self, key_num):
        return self._keys[key_num]

    def __iter__(self):
        return (k for (k, _) in enumerate(self._keys))

    def __len__(self):
        return len(self._keys)

    def fill(self, color):
        """Set all keys' NeoPixels to the specified color.

        :param int color: 24-bit color integer"""
        for pixel in self._pixels:
            pixel.fill(color)

    @property
    def brightness(self):
        """Brightness value shared by all NeoKey1x4 NeoPixels."""
        return self._brightness

    @brightness.setter
    def brightness(self, brightness):
        self._brightness = brightness
        for pixel in self._pixels:
            pixel.brightness = brightness

    def _set_auto_colors(self, auto_colors):
        """Set automatic color management function. When defined, is invoked on
        key press or release and is passed a single NeoKeyEvent as argument.

        :param function auto_colors: function expecting event returns color"""
        if auto_colors is not None:
            if not callable(auto_colors):
                raise TypeError("auto_colors must be a function")
            for key_num in self:
                # initialize to the released color
                self._keys[key_num].color = auto_colors(NeoKeyEvent(key_num, False))
        self._auto_colors = auto_colors

    def _set_auto_action(self, auto_action):
        """Set automatic action function. When defined, is invoked on key press
        or release and is passed a single NeoKeyEvent as argument.

        :param function auto_action: function expecting event as argument"""
        if auto_action is not None:
            if not callable(auto_action):
                raise TypeError("auto_action must be a function")
        self._auto_action = auto_action

    def read_keys(self):
        """Check activity of all keys on all NeoKey1x4 modules.
        Invokes optional auto_color and auto_action functions.
        Returns a list of NeoKeyEvent object corresponding keys pressed
        or released since the previous check."""
        events = []
        for index, seesaw in enumerate(self._seesaws):
            previous = self._key_bits[index]
            key_bits = seesaw.digital_read_bulk(_NEOKEY1X4_KEYMASK)
            key_bits ^= _NEOKEY1X4_KEYMASK  # invert
            key_bits &= _NEOKEY1X4_KEYMASK  # re-mask
            just = (
                (True, (key_bits ^ previous) & key_bits),
                (False, (key_bits ^ previous) & ~key_bits),
            )
            self._key_bits[index] = key_bits
            for pressed, bits in just:
                for key_num in _bits_to_keys(index, bits):
                    key_event = NeoKeyEvent(key_num, pressed)
                    events.append(key_event)
                    if self._auto_colors:
                        self._keys[key_num].color = self._auto_colors(key_event)
                    if self._auto_action:
                        self._auto_action(key_event)
        return events
