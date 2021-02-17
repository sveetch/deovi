.. _intro_install:

=======
Install
=======

Install package in your environment : ::

    pip install deovi

For development usage see :ref:`install_development`.

Configuration
*************

Add it to your installed Django apps in settings : ::

    INSTALLED_APPS = (
        ...
        'deovi',
    )

Then load default application settings in your settings file: ::

    from deovi.settings import *

And finally apply database migrations.

Settings
********

.. automodule:: deovi.settings
   :members:
