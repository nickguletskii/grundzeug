####################
Setting up Grundzeug
####################


Compatibility
=============

Grundzeug requires Python 3.7 or later.

Installing Grundzeug
====================

Grundzeug can be installed from github using pip:

.. code-block:: bash

    pip3 install git+https://github.com/nickguletskii/grundzeug.git

==================
mypy compatibility
==================

Grundzeug comes with a plugin for mypy that helps mypy process code annotated with Grundzeug's type annotations. You may enable it by creating a file called ``mypy.ini`` in your project's root directory with the following contents:


.. code-block:: ini

    [mypy]
    plugins = grundzeug.container.mypy_plugin