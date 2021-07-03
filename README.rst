Introduction
============


.. image:: https://readthedocs.org/projects/alt-circuitpython-neokey/badge/?version=latest
    :target: https://circuitpython-neokey.readthedocs.io/
    :alt: Documentation Status


.. image:: https://img.shields.io/discord/327254708534116352.svg
    :target: https://adafru.it/discord
    :alt: Discord


.. image:: https://github.com/gmparis/Alt_CircuitPython_NeoKey/workflows/Build%20CI/badge.svg
    :target: https://github.com/gmparis/Alt_CircuitPython_NeoKey/actions
    :alt: Build Status


.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
    :alt: Code Style: Black

Alternative CircuitPython API for NeoKey I2C Keypad


Dependencies
=============
This driver depends on:

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_
* `Bus Device <https://github.com/adafruit/Adafruit_CircuitPython_BusDevice>`_

Please ensure all dependencies are available on the CircuitPython filesystem.
This is easily achieved by downloading
`the Adafruit library and driver bundle <https://circuitpython.org/libraries>`_
or individual libraries can be installed using
`circup <https://github.com/adafruit/circup>`_.

Installing to a Connected CircuitPython Device with Circup
==========================================================

Make sure that you have ``circup`` installed in your Python environment.
Install it with the following command if necessary:

.. code-block:: shell

    pip3 install circup

With ``circup`` installed and your CircuitPython device connected use the
following command to install:

.. code-block:: shell

    circup install alt_neokey

Or the following command to update an existing version:

.. code-block:: shell

    circup update

Usage Example
=============

.. code-block:: py

   import board
   from alt_neokey.alt_neokey1x4 import NeoKey1x4

   i2c = board.I2C()
   neokey = NeoKey1x4(i2c)

   # set colors in main loop by processing event list
   while True:
      for event in neokey.read_keys():
         if event.pressed:
            neokey[event.key_num].color = 0x0000FF
         else:
            neokey[event.key_num].color = 0
         print(event.key_num, event.pressed)

Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/gmparis/Alt_CircuitPython_NeoKey/blob/HEAD/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.

Documentation
=============

For information on building library documentation, please check out
`this guide <https://learn.adafruit.com/creating-and-sharing-a-circuitpython-library/sharing-our-docs-on-readthedocs#sphinx-5-1>`_.
