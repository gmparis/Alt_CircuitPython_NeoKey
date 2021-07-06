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

from collections import namedtuple
from micropython import const
from adafruit_seesaw.seesaw import Seesaw
from adafruit_seesaw.neopixel import NeoPixel, GRB

try:
    from time import monotonic_ns  # pylint: disable=wrong-import-position
except ImportError:
    _HAS_MNS = False
else:
    try:
        monotonic_ns()
    except NotImplementedError:
        _HAS_MNS = False
    else:
        _HAS_MNS = True

if _HAS_MNS:

    def _time_ops_check(ignored=True):  # pylint: disable=unused-argument
        return True


else:

    def _time_ops_check(fatal=True):
        if fatal:
            raise RuntimeError("feature requires long integers")
        return False


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

NeoKeyEvent = namedtuple("NeoKeyEvent", "key_num pressed".split())
"""Event list element.

    :param int key_num: key number. 0-3 on first NeoKey, 4-7 on second, etc.
    :param bool pressed: *True* for key press event; *False* for key release event."""

# pylint: disable=missing-docstring


class NeoKeyKey:
    """A single key and pixel pairing.

    :param ~Seesaw.seesaw seesaw: NeoKey Seesaw
    :param ~Seesaw.neopixel pixel: NeoKey NeoPixel
    :param int key_num: key number assigned by *NeoKey1x4*

    The constructor for this class is not intended to be invoked
    by anything other than *NeoKey1x4*. One *NeoKeyKey* instance
    is created by *NeoKey1x4* for each key. Keys are numbered 0-3
    on the first NeoKey module. 4-7 on the second, etc.

    These instances can be referenced by indexing a *NeoKey1x4*
    object, as shown in the examples below.

    .. sourcecode:: python

        neokey = NeoKey1x4(i2c, addr=[0x30, 0x31, 0x32])

        neokey[0].color = 0xFF0000 # make red
        neokey[11].blink = True # start blinking

        key = neokey[0] # reference a NeoKeyKey instance
        key.color = 0xFF0000 # same as above example

        # key numbers of keys pressed now
        pressed = [k for k in neokey if neokey[k].pressed]

    """

    __slots__ = ("_seesaw", "_pixel", "_key_num", "_blink")

    def __init__(self, seesaw, pixel, key_num, *, blink=False):
        self._seesaw = seesaw
        self._pixel = pixel
        self._key_num = int(key_num)
        if blink:
            _time_ops_check()  # to exception if necessary
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
        """Integer key number assigned by *NeoKey1x4*. Read-only."""
        return self._key_num

    @property
    def pressed(self):
        """Immediate read of this key's state via the I2C bus.
        Read-only property is *True* if the key is being pressed.
        Does not invoke or affect **auto_color** or **auto_action**."""
        key_bits = self._seesaw.digital_read_bulk(_NEOKEY1X4_KEYMASK)
        key_bits ^= _NEOKEY1X4_KEYMASK  # invert
        return (key_bits & _NEOKEY1X4_KEYS[self._key_num]) != 0

    @property
    def color(self):
        """Read-write integer property representing the key's pixel color.
        Reads and writes are done over the I2C bus."""
        return self._pixel[self._key_num]

    @color.setter
    def color(self, color):
        self._pixel[self._key_num] = int(color)

    @property
    def blink(self):
        """Read-write boolean property, *True* when key is blinking."""
        return self._blink

    @blink.setter
    def blink(self, blink):
        blink = bool(blink)
        if blink:
            _time_ops_check()  # to exception if necessary
        self._blink = blink


def _bits_to_keys(seesaw_num, bits):
    offset = seesaw_num * _NEOKEY1X4_COUNT
    return [(k + offset) for k in range(_NEOKEY1X4_COUNT) if _NEOKEY1X4_KEYS[k] & bits]


class NeoKey1x4:
    """Alternative API for Adafruit's I2C keypad with RGB LEDs.

    :param ~busio.I2C i2c_bus: Bus the NeoKey is connected to
    :param int addr: I2C address (or list of addresses) of NeoKey 1x4 module(s)
    :param float brightness: RGB LED intensity
    :param function auto_color: set colors when keys pressed/released
    :param function auto_action: run when keys pressed/released
    :param bool blink: blink all keys when they are not pressed

    The intent of this alternative API is to reduce the amount of user
    code necessary to manage key colors and respond to key-press events.
    It also simplifies the task of managing more than one NeoKey module
    simultaneously. The cost is that this library uses more memory than
    the standard does. Comparing *simpletest* examples from the two libraries,
    this alternative uses about 8 KB more memory. The all-bells-and-whistles
    *blinktest* example uses another 3 KB.

    Basic usage is one NeoKey module. In that case, supply its I2C address
    as the **addr** argument.

    To use multiple modules together, supply a list or tuple of I2C addresses
    as the **addr** argument. Sixteen modules can be supported by selectively
    solder-bridging the four address selectors to give each board a unique
    address, 0x30 through 0x3F. Key numbers will be assigned to the keys in
    the order of board addresses in the list, first 0-3, second 4-7, ...,
    sixteenth 60-63. (If you accidentally assemble your project with the
    modules out of ascending address order, no worries! Just order them the
    same way in the **addr** list; the keys will be numbered the way you want.)

    Keys may be referenced by indexing the *NeoKey1x4* instance. Each key is
    represented by a *NeoKeyKey* instance. See the section about that class
    for its attributes.

    To dynamically manipulate key colors without coding it into your main
    loop, create a function that returns a color (24-bit RGB) and pass it
    to the *NeoKey1x4* constructor using the **auto_color** parameter. The function
    will be called for each key press and key release event, as detected by
    the **read()** method. That method will call the function with a single
    argument, a *NeoKeyEvent*.

    Similarly, to have **read()** run arbitrary code whenever a key is pressed,
    use the *NeoKey1x4* constructor's **auto_action** parameter. Any return value
    from the function will be ignored. As with **auto_color**, it will be passed
    a single *NeoKeyEvent* argument when invoked.

    The **blink** parameter is provided to initially enable all keys to blink
    while not being pressed, as sensed by **read()**. Keys may be set
    individually to blink or not blink using their **blink** property,
    regardless of the **blink** value passed to the *NeoKey1x4* constructor.
    The blink feature requires **time.monotonic_ns()**, which is not available
    on some boards. In that case, the feature is disabled and attempting
    to use it will raise a *RuntimeError* exception.

    .. note:: The **auto_color** function is used to initialize key colors
        whenever it is set or changed (except when set to *None*).
        It is used with blink mode to establish the 'on' color in the on/off
        cycle. In contrast, the **auto_action** function can be relied upon
        to be called only on key press and key release events.

    Any time spent doing anything other than reading keys can detract from
    the responsiveness of the keys. It is probably a good idea to have keys
    change color when they are pressed, so that the user gets immediate
    feedback that the key press has been registered.

    The following example code has the keys light white when pressed.

    .. sourcecode:: python

        import board
        from alt_neokey.alt_neokey1x4 import NeoKey1x4
        i2c = board.I2C()
        neokey = NeoKey1x4(
            i2c,
            auto_color=lambda e: 0xFFFFFF if e.pressed else 0
        )
        while True:
            neokey.read()
    """

    # blink rate could be problematic depending on work load,
    # processor power, and number of NeoKey modules, so the
    # parameters are set in the class in case the user wishes
    # to override them in their instance
    blink_period = 20
    blink_on = 14

    def _blink_clock(self):
        """True when blink is in 'on' state."""
        return (monotonic_ns() // 100_000_000) % self.blink_period < self.blink_on

    def __init__(
        self,
        i2c_bus,
        addr=_NEOKEY1X4_BASE_ADDR,
        *,
        brightness=0.2,
        auto_color=None,
        auto_action=None,
        blink=False,
    ):
        try:
            if len(set(addr)) < len(addr):
                raise RuntimeError("duplicates in I2C address list")
        except TypeError:
            addr = (addr,)
        if blink:
            _time_ops_check()  # to exception if necessary
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
        self.auto_color = auto_color
        self.auto_action = auto_action

    def __getitem__(self, key_num):
        return self._keys[key_num]

    def __iter__(self):
        return (k for (k, _) in enumerate(self._keys))

    def __len__(self):
        return len(self._keys)

    def fill(self, color):
        """Set all keys to the specified color.
        Useful when setting key colors other than with **auto_color**.

        :param int color: 24-bit color integer"""
        for pixel in self._pixels:
            pixel.fill(color)

    @property
    def brightness(self):
        """Float brightness value shared by all NeoKey LEDs."""
        return self._brightness

    @brightness.setter
    def brightness(self, brightness):
        self._brightness = brightness
        for pixel in self._pixels:
            pixel.brightness = brightness

    @property
    def auto_color(self):
        """Automatic color management function. Function is invoked on
        key press or release and is passed a single *NeoKeyEvent* as argument.
        The function must return a 24-bit RGB color integer.
        Use *None* to remove a previously set **auto_color** function.
        All keys are immediately set to their 'released' color whenever
        this parameter is set to a value other than *None*.

        The code snippet below, taken from one of the example programs,
        shows key 0 being used to toggle between two key-color modes.

        .. sourcecode:: python

            while True:
                for event in neokey.read():
                    if event.pressed and event.key_num == 0:
                        if neokey.auto_color is normal_mode:
                            neokey.auto_color = special_mode
                        else:
                            neokey.auto_color = normal_mode

        """
        return self._auto_color

    @auto_color.setter
    def auto_color(self, function):
        if function is not None:
            if not callable(function):
                raise TypeError("auto_color value must be a function")
            for key_num in self:
                # initialize to the released color
                self._keys[key_num].color = function(NeoKeyEvent(key_num, False))
        self._auto_color = function

    @property
    def auto_action(self):
        """Automatic action function. Function is invoked on key press
        or release and is passed a single *NeoKeyEvent* as argument.
        The return value of this function is ignored.
        Use *None* to remove a previously set function."""
        return self._auto_action

    @auto_action.setter
    def auto_action(self, function):
        if function is not None:
            if not callable(function):
                raise TypeError("auto_action value must be a function")
        self._auto_action = function

    def _blink_now(self):
        """Determine if now is the time to blink."""
        do_blink = False
        if _time_ops_check(False):  # non-fatal check
            blink_wanted = self._blink_clock()
            if blink_wanted != self._blink_state:
                do_blink = True
                self._blink_state = blink_wanted
        return do_blink

    def _blink_key(self, key_num, state):
        """If state *True*, turn on color using **auto_color**, preferring released color,
        then pressed color. If both colors are 0 (off), or if no **auto_color**, use white."""
        if not state:
            color = 0  # off is always off
        elif self._auto_color:
            color = 0xFFFFFF  # on is default white
            for pressed in (False, True):
                action_color = self._auto_color(NeoKeyEvent(key_num, pressed))
                if action_color:
                    color = action_color
                    break
        self._keys[key_num].color = color

    def _read_module(self, index, seesaw, do_blink):
        """Common code for **read()** and **read_event()**.
        Reads one module, executes **auto_** functions. Blinks.
        Returns event list."""
        events = []
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
                if self._auto_color:
                    self._keys[key_num].color = self._auto_color(key_event)
                if self._auto_action:
                    self._auto_action(key_event)
        if do_blink:
            for key_num in _bits_to_keys(index, unpressed_bits):
                if self._keys[key_num].blink:
                    self._blink_key(key_num, self._blink_state)
        return events

    def read(self):
        """At the most basic level, **read()** queries all keys via
        the I2C bus. It compares the states of the keys to the previous
        time it was run. From that comparison, it generates an event
        list. Each event in that list corresponds to a key press or
        key release. This is not the same as the current state of a
        key, as a key that was neither pressed nor released since the
        last **read()** will not have an event in the list. (To get
        the current state of a key, use its **pressed** property.)
        Each event in the list is a *NeoKeyEvent* instance. The return
        value is this list.

        The following code snippet, adapted from the *simpletest* example,
        demonstrates responding to the event list returned by **read()**.

        .. sourcecode:: python

            while True:
                for event in neokey.read():
                    if event.pressed:
                        print(f"key {event.key_num} pressed")
                        do_something_useful()
                    else:
                        print(f"key {event.key_num} released")

        The NeoKey module has an RGB LED under each key. Many uses would
        have the keys change colors when keys are pressed and released.
        This can be achieved in your main program, but cluttering it up
        with key-color management will make it harder to see
        the code that's there for the main purpose of your program.

        Instead, define a function that returns a color based on (or
        ignoring) the single *NeoKeyEvent* argument that will be passed
        to the function when it is invoked. Then, either as an argument
        to the *NeoKey1x4* constructor or by using its **auto_color**
        property, you inform the *NeoKey1x4* to use this function to
        set key colors. It will invoke the function on key press and
        key release events, setting the color of the key in question.

        This function in many cases is so simple that it can be expressed
        as a *lambda*, as in the code snippet below, which sets the
        key color to red when pressed and off when released.

        .. sourcecode:: python

            neokey.auto_color = lambda e: 0xFF0000 if e.pressed else 0

        Another thing *NeoKey1x4* can do for you is blink your keys.
        For example, to signal an alert condition associated with a
        key, the **blink** property of that key could be set to *True*.
        Each time **read()** is run, it checks to see whether the key
        should change from 'off' to 'on' or vice versa and takes care
        of it.

        .. sourcecode:: python

            neokey[2].blink = True # sets key 2 blinking

        Finally, similar to **auto_color**, **read()** can execute a
        function every time a key is pressed or released. This
        can be set in an argument to the *NeoKey1x4* constructor
        or it can be specified using the **auto_action** property.

        Although there is no limitation on uses for this function, a
        suggestion is to use it for other housekeeping functions,
        such as key-clicks, haptic feedback, key logging, etc. This
        would allow you to keep such code separate from the main thrust
        of your program. Any return value from the **auto_action**
        function will be ignored.

        .. sourcecode:: python

            def sound_on_pressed(kev):
                if kev.pressed:
                    if kev.key_num == 0:
                        my_ring_bell()
                    else:
                        my_key_click()

            neokey.auto_action = sound_on_pressed
        """

        events = []
        do_blink = self._blink_now()
        for index, seesaw in enumerate(self._seesaws):
            events.extend(self._read_module(index, seesaw, do_blink))
        return events

    def read_event(self, *, timeout=0):
        """Similar to **read()** in its calling of **auto_**
        functions and managing **blink**, but uses a different approach
        to gathering and returning events.

        :param int timeout: yield *None* if no key activity in 10ths of a second

        This method queries one NeoKey module at a time. If there are
        events from that module, yields those events back to the caller
        *one event at a time*. On the next call, it starts where it left
        off. It continues to the next module, starting over with the
        first after the last, looping forever.

        The principal advantage of **read_event()** over **read()**
        is latency fairness. With **read()**, the first NeoKey module
        gets quicker response than the last because **auto_color**,
        **auto_action** and **blink** are processed in module
        and key order. (This effect also could be present in your
        main program, if it processes the event list in order.)
        With **read_event()**, latency is shared evenly because it
        always picks up from where it left off.

        .. note:: A possibly critical disadvantage of using
            **read_event()** is that it does not return to the caller
            until it detects an event.

            To overcome this behavior, use the **timeout** parameter
            to cause **read_event()** to return *None* whenever the
            specified time has elapsed without a key event. As with
            **blink**, **timeout** is supported only when the board
            supports **time.monotonic_ns()**.

        Depending on your application, latency differences might be
        insignificant or unimportant. In those cases, you probably
        should use **read()**, as it allows for more flexibility in
        the main program, given that the **timeout** feature is not
        universally supported.

        Here is an example of using **read_event()** with a timeout
        of three tenths of a second.

        .. sourcecode:: python

            # no need for "while True:"
            for event in neokey.read_event(timeout=3):
                if event is not None:
                    ... # handle key event here
                ... # do other tasks

        """

        if timeout:
            _time_ops_check()  # fatal if not supported
            timeout = int(timeout)
            if timeout < 0:
                raise ValueError("negative timeout")
            last_event = monotonic_ns()
        while True:
            do_blink = self._blink_now()
            for index, seesaw in enumerate(self._seesaws):
                if timeout:
                    now = monotonic_ns()
                for event in self._read_module(index, seesaw, do_blink):
                    if timeout:
                        last_event = now
                    yield event
                if timeout:
                    if (now - last_event) // 100_000_000 >= timeout:
                        last_event = now
                        yield None  # no events sentinel
