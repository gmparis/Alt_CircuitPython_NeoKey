# SPDX-FileCopyrightText: Copyright (c) 2021 Greg Paris
#
# SPDX-License-Identifier: MIT
"""
`alt_neokey.alt_neokey1x4`
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

try:
    from time import monotonic_ns
except ImportError:

    def _blink_check(fatal=True):
        if fatal:
            raise RuntimeError("blink requires monotonic_ns")
        return False


else:

    def _blink_check(ignored=True):  # pylint: disable=unused-argument
        return True


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

    :param int key_num: key number. 0-3 on first NeoKey, 4-7 on second, etc.
    :param bool pressed: True for key press event; False for key release event."""

# pylint: disable=missing-docstring


class NeoKeyKey:
    """A single key+pixel pairing.

    :param ~Seesaw.seesaw seesaw: NeoKey Seesaw
    :param ~Seesaw.neopixel pixel: NeoKey NeoPixel
    :param int key_num: key number assigned by NeoKey1x4

    One NeoKeyKey instance is created by NeoKey1x4 for each key.
    Keys are numbered 0-3 on the first NeoKey. 4-7 on the second, etc.

    These instances can be referenced by indexing the NeoKey1x4
    object, as shown here.

    .. sourcecode:: python

        neokey = NeoKey1x4(i2c)
        neokey[0].color = 0xFF0000 # set color
        neokey[1].blink = True # turn on blinking
        key = neokey[2] # reference a NeoKeyKey instance
        print(key.pressed) # True while the key is pressed
    """

    __slots__ = ("_seesaw", "_pixel", "_key_num", "_blink")

    def __init__(self, seesaw, pixel, key_num, *, blink=False):
        self._seesaw = seesaw
        self._pixel = pixel
        self._key_num = int(key_num)
        if blink:
            _blink_check()  # to exception if necessary
        self._blink = bool(blink)

    def __lt__(self, other):
        # this is here for sorting of NeoKeyKeys (hmmm...)
        # Key nums are unique for a single NeoKey1x4 instance,
        # but could somebody have two? That's why _seesaw is here.
        return (self._key_num, self._seesaw) < (other._key_num, other._seesaw)

    def __eq__(self, other):
        # this is here so keys can be put in a set used as a dict key
        return (self._key_num, self._seesaw) == (other._key_num, other._seesaw)

    def __hash__(self):
        # this is here so keys can be put in a set used as a dict key
        return hash((self._key_num, self._seesaw))

    @property
    def key_num(self):
        """Key number assigned by NeoKey1x4. Read-only."""
        return self._key_num

    @property
    def pressed(self):
        """Immediate read of this key's state via the I2C bus.
        Read-only property is True if the key is being pressed.
        Does not invoke or otherwise affect auto_colors or auto_action."""
        key_bits = self._seesaw.digital_read_bulk(_NEOKEY1X4_KEYMASK)
        key_bits ^= _NEOKEY1X4_KEYMASK  # invert
        return (key_bits & _NEOKEY1X4_KEYS[self._key_num]) != 0

    @property
    def color(self):
        """Read-write property representing the key's pixel color.
        Reads and writes are done over the I2C bus."""
        return self._pixel[self._key_num]

    @color.setter
    def color(self, color):
        self._pixel[self._key_num] = int(color)

    @property
    def blink(self):
        """Read-write property, True when key is blinking."""
        return self._blink

    @blink.setter
    def blink(self, blink):
        blink = bool(blink)
        if blink:
            _blink_check()  # to exception if necessary
        self._blink = blink


def _bits_to_keys(seesaw_num, bits):
    offset = seesaw_num * _NEOKEY1X4_COUNT
    return [(k + offset) for k in range(_NEOKEY1X4_COUNT) if _NEOKEY1X4_KEYS[k] & bits]


def _blink_now():
    """Odd seconds on, even seconds off"""
    return bool((monotonic_ns() // 1_000_000_000) % 2)


class NeoKey1x4:
    """Alternative API for Adafruit's I2C keyboard with NeoPixel lights.

    :param ~busio.I2C i2c_bus: Bus the NeoKey is connected to
    :param int addr: I2C address (or list of addresses) of NeoKey 1x4 module(s)
    :param float brightness: NeoPixel intensity
    :param function auto_colors: set colors when keys pressed/released
    :param function auto_action: run when keys pressed/released
    :param bool blink: blink all keys when they are not pressed

    The intent of this alternative API is to put functionality that users
    would have to code into their main loops into this library, simplifying
    use, though at the cost of memory. For newer CircuitPython hardware,
    memory is more plentiful, so increased memory use may not be a concern.

    Basic usage is one NeoKey module. In that case, supply its I2C address
    as the addr argument.

    To use more than one module at once, instead supply a list (or tuple) of
    I2C addresses as the addr argument. Up to eight modules can be supported
    by solder-bridging the address selectors to give each board a unique
    address. Key numbers will be assigned to the keys in the order of board
    addresses in the list, first 0-3, second 4-7, ..., eighth 28-31.

    Keys may be referenced by indexing the NeoKey1x4 instance. Each key is
    represented by a NeoKeyKey instance. See that section for the attributes
    of those objects.

    To dynamically manipulate key colors without coding it into your main
    loop, create a function that returns a color (24-bit RGB) and pass it
    to the NeoKey1x4 constructor using the auto_colors parameter. The function
    will be called for each key press and key release event, as detected by
    the read_keys method. That method will call the function with a single
    argument, a NeoKeyEvent.

    Similarly, to have read_keys run arbitrary code whenever a key is pressed,
    use the NeoKey1x4 constructor's auto_action parameter. Any return value
    from the function will be ignored. As with auto_colors, it will be passed
    a single NeoKeyEvent argument.

    The blink parameter is provided to initially enable all keys to blink
    while not being pressed, as sensed by read_keys. Keys may be set
    individually to blink or not blink using their blink property,
    regardless of the blink setting passed to the NeoKey1x4 constructor.
    The blink feature requires time.monotonic_ns, which is not available
    on some boards. In that case, the feature is disabled and attempting
    to use it will raise a RuntimeError exception.

    NOTE: The auto_colors function, if defined, is used to initialize
    key colors. It is also used with blink mode to establish the
    'on' color in the on/off cycle. For predictable results, the auto_colors
    function should be re-entrant and without side effects. In contrast,
    the auto_action function can be relied upon to be called only on
    key press and key release events.

    Any time spent doing anything other than reading keys can detract from
    the responsiveness of the keys. It's probably a good idea to have keys
    change color when they are pressed, so that the user gets immediate
    feedback that the key press has been registered.

    The following example code has the keys light white when pressed.

    .. sourcecode:: python

        import board
        from alt_neokey.alt_neokey1x4 import NeoKey1x4
        i2c = board.I2C()
        neokey = NeoKey1x4(
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
        blink=False,
    ):
        try:
            if len(set(addr)) < len(addr):
                raise RuntimeError("duplicates in I2C address list")
        except TypeError:
            addr = (addr,)
        if blink:
            _blink_check()  # to exception if necessary
        self._blink_state = True  # lights on
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
                keys.append(NeoKeyKey(ss_mod, np_mod, key_num, blink=blink))
        self._seesaws = tuple(seesaws)
        self._pixels = tuple(pixels)
        self._keys = tuple(keys)
        self._brightness = float(brightness)
        self._key_bits = [0x0] * len(seesaws)
        self.set_auto_colors(auto_colors)
        self.set_auto_action(auto_action)

    def __getitem__(self, key_num):
        return self._keys[key_num]

    def __iter__(self):
        return (k for (k, _) in enumerate(self._keys))

    def __len__(self):
        return len(self._keys)

    def fill(self, color):
        """Set all keys to the specified color.
        Useful when setting key colors other than with auto_colors.

        :param int color: 24-bit color integer"""
        for pixel in self._pixels:
            pixel.fill(color)

    @property
    def brightness(self):
        """Brightness value shared by all NeoKey NeoPixels."""
        return self._brightness

    @brightness.setter
    def brightness(self, brightness):
        self._brightness = brightness
        for pixel in self._pixels:
            pixel.brightness = brightness

    def set_auto_colors(self, auto_colors):
        """Set automatic color management function. When defined, is invoked on
        key press or release and is passed a single NeoKeyEvent as argument.
        Use None to remove a previously set function.

        :param function auto_colors: function expecting event, returns color"""
        if auto_colors is not None:
            if not callable(auto_colors):
                raise TypeError("auto_colors must be a function")
            for key_num in self:
                # initialize to the released color
                self._keys[key_num].color = auto_colors(NeoKeyEvent(key_num, False))
        self._auto_colors = auto_colors

    def set_auto_action(self, auto_action):
        """Set automatic action function. When defined, is invoked on key press
        or release and is passed a single NeoKeyEvent as argument.
        Use None to remove a previously set function.

        :param function auto_action: function expecting event as argument"""
        if auto_action is not None:
            if not callable(auto_action):
                raise TypeError("auto_action must be a function")
        self._auto_action = auto_action

    def read_keys(self):
        """Check activity of all keys on all NeoKey modules.
        Invokes optional auto_colors and auto_action functions.
        Returns a list of NeoKeyEvent object corresponding keys pressed
        or released since the previous check."""
        events = []
        do_blink = False
        if _blink_check(False):  # non-fatal check
            blink_wanted = _blink_now()
            if blink_wanted != self._blink_state:
                do_blink = True
                self._blink_state = blink_wanted
        for index, seesaw in enumerate(self._seesaws):
            previous = self._key_bits[index]
            # due to pull-ups, pressing a key sets its bit to 0
            unpressed_bits = key_bits = seesaw.digital_read_bulk(_NEOKEY1X4_KEYMASK)
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
            if do_blink:
                for key_num in _bits_to_keys(index, unpressed_bits):
                    if self._keys[key_num].blink:
                        self._blink_key(key_num, blink_wanted)
        return events

    def _blink_key(self, key_num, state):
        """If state True, turn on color using auto_colors or white; otherwise dark"""
        if not state:
            color = 0
        elif self._auto_colors:
            color = self._auto_colors(NeoKeyEvent(key_num, False))  # released
            if not color:  # doesn't work if unpressed color is dark
                color = 0xFFFFFF
        else:
            color = 0xFFFFFF
        self._keys[key_num].color = color
