.. _django-deovi: https://github.com/sveetch/django-deovi

.. _intro_collector:

=========
Collector
=========

The purpose of this tool is to recursively collect informations about resource files
from a path.

.. Note::
    Collector does not open files to get their meta informations, it just collect their
    filesystem informations (date, paths, size, etc..).

Although the tool output some kind of resume, the main goal is to dump collection to a
JSON file that can be used programmatically such as with `django-deovi`_, a Django
project that allow to browse collected resources (once imported).

.. _collector_resourcer_type:

Resource types
**************

There are currently three types of resources that can be collected.

Serie
-----

Is for a directory that contains media files, it is assumed each of the media file is
an episode.

Its manifest is expected to be named ``manifest.json`` located in the Collection
directory.

Movie
-----

Is for a media file supported from :ref:`collector_media_kind`.

Its manifest is expected to be named like its related media files with extension
changed to ``.json`` or ``.yaml``, depending the manifest format. The manifest file
should be located along the media file in the same directory.

Collection
----------

Is for a directory that contains media files, but opposed to a Serie, a collection can
not be scrapped because it does not exists in TMDB. See it more like a virtual resource
that allows you to regroup a collection of movies, like for a saga (Star Wars, Alien,
etc..).

Its manifest is expected to be named ``manifest.json`` located in the Collection
directory.

.. _collector_media_kind:

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
directories (for Serie or Collection) that have at least a single media file.

All directories that don't have any supported media files will be ignored from
collecting.


Manifest
********

Each directory may contains a manifest file (either JSON or YAML) to include some
directory meta information to include in the dump.

Each resource may have a related manifest, no matter its type. Serie and Collection
resource are dedicated to a directory while Movie is only for a media file (as
supported from :ref:`collector_media_kind`).

The manifest content is almost free except it can not defines item names that are
computed from collection to avoid overwriting.

.. Warning::
    If you are planning to use :ref:`intro_scrapping` be aware that it will overwrite
    the manifest file and all your custom values will be lost.

Forbidden item names in manifest are:

* ``cover``;
* ``name``;
* ``path``;
* ``parent``;


Cover
*****

Each resource may have a cover image file to collect if its manifest defines one.

.. Hint::
    It is recommended to optimize your cover image file sizes.


Directory checksum
******************

If this options is enabled a checksum will be computed for each resource.

Serie and Collection build a checksum from all gathered informations. This means basic
directory informations (paths, size, etc..) but also additional data from possible
manifest and cover file.

The directory checksum is included in directory payload from dump and the cover file
checksum also. Cover checksum is used to compute the directory one but is available
also in directory payload as an helper to just check for cover file change.

Usage
*****

Command requires two positionnal arguments in this order:

* ``source``: A directory path to scan recursively for resources;
* ``destination``: A file path for the JSON dump to create. If resources have a cover,
  a new directory will be created along the JSON dump file to store all the cover files;

And possible keyword arguments:

* ``--checksum``: If given this will enable directory checksum. On default checksum
  is disabled;

Sample command usage: ::

    deovi collect my_device plop.json --checksum

Sample
******

This is a sample of proper structure to collect: ::

    my_device/
    ├── cover.png
    ├── manifest.yaml
    ├── SampleVideo.mkv
    ├── nope/
    ├── the-serie/
    │   ├── cover.png
    │   ├── manifest.yaml
    │   ├── episode01.mkv
    │   └── episode02.mp4
    ├── other-serie/
    │   ├── cover.png
    │   ├── manifest.yaml
    │   ├── episode01.mkv
    │   ├── episode02.mkv
    │   ├── episode03.mp4
    │   └── episode04.mp4
    └── classics/
        ├── cover.jpg
        ├── Casablanca.mkv
        ├── Casablanca.yaml
        ├── manifest.yaml
        ├── The-pit.json
        └── The-pit.mkv

``my_device`` would be collected as the root, named ``.``. We don't recommend to have
resource at the root since ``.`` is not a significant name.

``nope`` directory won't be collected because it does not have any supported files (no
media or manifest). Everything else should be collected.

For example ``other-serie/manifest.yaml`` would be collected as the ``other-serie``
manifest, ``classics/Casablanca.yaml`` could be collected as the
manifest of ``classics/Casablanca.mkv`` (if valid) and ``classics/cover.jpg`` as the
``classics/`` cover if its manifest define it as so.

The resulting dump will contains a registry of collected resources, each resource gather
its filesystem information and possible manifest information.

And a directory like ``my_device_7a4067f264f889051f91/`` will be created with all cover
files from all resources: ::

    my_device_7a4067f264f889051f91/
    ├── 54d4d2a3-5c13-4c8e-9b8f-d4877edf24d6.png
    ├── 19eecca3-c610-7c44-9b8f-4c67f247ed64.png
    ├── d6a67d9c-1590-4c67-9c93-37a4da5a01f9.png
    └── c92308e0-c385-441b-ba7c-a79babf94c6e.jpg

The cover directory name is created including the dump file name with a hash so it is
guaranteed to be unique every time you run the collect command.

If you have to import this dump in some other tools like `django-deovi`_, you will
transfer the directory along the dump, so the tool will be able to load cover files as
described in the dump. Note than the directory cover path are relative to dump file so
you should not move it elsewhere or you will have to edit the dump yourself.

