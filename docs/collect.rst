.. _django-deovi: https://github.com/sveetch/django-deovi

.. _intro_collector:

=========
Collector
=========

This tool purpose is to recursively collect informations about media files from a path,
media files will be stored and organized internally per directory. Note than collector
does not open files to get their meta informations, it just collect their filesystem
informations (date, paths, size, etc..).

Although the tool can output some kind of collection resume, the real feature is to
dump collection to a JSON file that can be used programmatically.

This JSON dump is supported by `django-deovi`_, a Django project that can be used to
browse collection once imported.


Media kind
**********

At this point, the only recognized media file kinds are the common video formats.

* ``3gp``: 3GPP;
* ``asf``: Advanced Systems Format;
* ``avi``: AVI;
* ``flv``: Flash Video;
* ``f4v``: Flash Video;
* ``mov``: QuickTime;
* ``mp4``: MPEG-4;
* ``mkv``: Matroska;
* ``mpg``: MPEG;
* ``mpeg``: MPEG;
* ``mpv``: MPEG;
* ``mts``: MPEG Transport Stream;
* ``qt``: QuickTime;
* ``rm``: RealMedia;
* ``ts``: MPEG Transport Stream;
* ``vob``: Vob;
* ``webm``: WebM;
* ``wmv``: Windows Media Video;

By default, collector will collect every file that match these video format extensions.

You may however select only a few of them with command argument ``--extension``.


Empty directories
*****************

The collector is running recursively on given path to scan and it will only retains
directories which have at least a single media file. All directories that don't have
any supported media files will be ignored from collection.


Directory cover
***************

Each directory may have a cover image file to collect. A cover is only owned by its
direct directory, children directories won't inherit its parent one.

Collector recognize a file as a cover if it is named ``cover`` and have extension
``png``, ``jpg``, ``jpeg`` or ``gif``. If there is multiple elligible cover files in
the same directory, collector will choose the one with the extension priority as
described from previous extension list order.

.. Note::
    It is recommended to optimize your cover image file sizes.


Directory manifest
******************

Each directory may contains a YAML file ``manifest.yml`` to include some directory meta
informations to include in the dump. The manifest content is almost free except it can
not defines item names that are computed from collection to avoid overwriting.

Forbidden item names are:

* ``absolute_dir``;
* ``children_files``;
* ``cover``;
* ``mtime``;
* ``name``;
* ``path``;
* ``relative_dir``;
* ``size``;


Usage
*****

Command requires two positionnal arguments in this order:

* ``source``: A path to a directory to scan recursively for collection;
* ``destination``: A path to file that will be created with the JSON dump. Note that if
  you have directory covers, a new directory will be created along the JSON dump file
  to store all the cover files;

So with the following command: ::

    deovi collect my_device plop.json

For the following ``my_device/`` directory content: ::

    my_device/
    ├── cover.png
    ├── foo/
    │   ├── bar/
    │   │   └── nope.txt
    │   ├── cover.png
    │   ├── manifest.yaml
    │   └── SampleVideo_720x480_1mb.mp4
    ├── manifest.yaml
    ├── ping/
    │   └── pong/
    │       ├── cover.gif
    │       ├── SampleVideo_720x480_1mb.mkv
    │       └── SampleVideo_720x480_2mb.mkv
    └── SampleVideo_1280x720_1mb.mkv

It would create a ``plop.json`` file with a JSON collection dump alike this: ::

    {
        "foo": {
            "path": "/home/donald/my_device/foo",
            "name": "foo",
            "absolute_dir": "/home/donald/my_device",
            "relative_dir": "foo",
            "size": 4096,
            "mtime": "2023-03-03T15:28:31+00:00",
            "children_files": [
                {
                    "path": "/home/donald/my_device/foo/SampleVideo_720x480_1mb.mp4",
                    "name": "SampleVideo_720x480_1mb.mp4",
                    "absolute_dir": "/home/donald/my_device/foo",
                    "relative_dir": "foo",
                    "directory": "foo",
                    "extension": "mp4",
                    "container": "MPEG-4",
                    "size": 1057149,
                    "mtime": "2023-03-03T15:28:31+00:00"
                }
            ],
            "title": "Foo bar",
            "cover": "my_device_7a4067f264f889051f91/c6a67d9c-1590-4c67-9c93-37a4da5a01f9.png"
        },
        "ping/pong": {
            "path": "/home/donald/my_device/ping/pong",
            "name": "pong",
            "absolute_dir": "/home/donald/my_device/ping",
            "relative_dir": "ping/pong",
            "size": 4096,
            "mtime": "2023-03-03T15:28:31+00:00",
            "children_files": [
                {
                    "path": "/home/donald/my_device/ping/pong/SampleVideo_720x480_2mb.mkv",
                    "name": "SampleVideo_720x480_2mb.mkv",
                    "absolute_dir": "/home/donald/my_device/ping/pong",
                    "relative_dir": "ping/pong",
                    "directory": "pong",
                    "extension": "mkv",
                    "container": "Matroska",
                    "size": 2106944,
                    "mtime": "2023-03-03T15:28:31+00:00"
                },
                {
                    "path": "/home/donald/my_device/ping/pong/SampleVideo_720x480_1mb.mkv",
                    "name": "SampleVideo_720x480_1mb.mkv",
                    "absolute_dir": "/home/donald/my_device/ping/pong",
                    "relative_dir": "ping/pong",
                    "directory": "pong",
                    "extension": "mkv",
                    "container": "Matroska",
                    "size": 1050238,
                    "mtime": "2023-03-03T15:28:31+00:00"
                }
            ],
            "cover": "my_device_7a4067f264f889051f91/c92308e0-c385-441b-ba7c-a79babf94c6e.gif"
        },
        ".": {
            "path": "my_device",
            "name": "my_device",
            "absolute_dir": ".",
            "relative_dir": ".",
            "size": 4096,
            "mtime": "2023-03-03T15:28:31+00:00",
            "children_files": [
                {
                    "path": "/home/donald/my_device/SampleVideo_1280x720_1mb.mkv",
                    "name": "SampleVideo_1280x720_1mb.mkv",
                    "absolute_dir": "/home/donald/my_device",
                    "relative_dir": ".",
                    "directory": "",
                    "extension": "mkv",
                    "container": "Matroska",
                    "size": 1052413,
                    "mtime": "2023-03-03T15:28:31+00:00"
                }
            ],
            "title": "Media sample root",
            "cover": "my_device_7a4067f264f889051f91/54d4d2a3-5c13-4c8e-9b8f-d4877edf24d6.png"
        }
    }

.. Note::
    As you can see from this dump sample, there is a directory entry ``.``, which is
    for the collected file from the root of source argument ``my_device``.

    We recommend you to organize your directory structure to avoid having files at root
    of source because ``.`` is not a very meaning name.

And a directory ``plop_ad79e25c5391ea259df8/`` which include cover files: ::

    my_device_7a4067f264f889051f91/
    ├── 54d4d2a3-5c13-4c8e-9b8f-d4877edf24d6.png
    ├── c6a67d9c-1590-4c67-9c93-37a4da5a01f9.png
    └── c92308e0-c385-441b-ba7c-a79babf94c6e.gif

The cover directory name is created including the dump file name with a hash so it is
guaranteed to be unique every time you run the collect command.

If you have to import this dump in some other tools like `django-deovi`_, you will
transfer the directory along the dump, so the tool will be able to load cover files as
described in the dump. Note than the directory cover path are relative to dump file so
you should not move it elsewhere or you will have to edit the dump yourself.

