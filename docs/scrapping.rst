.. _TMDb: https://www.themoviedb.org/
.. _TMDb API: https://developer.themoviedb.org/docs/getting-started

.. _intro_scrapping:

=========
Scrapping
=========

The scrapping tool stands on `TMDb API`_ to get TV serie details and cover. Details
are written into a manifest file along the cover at the given destination directory.

The first purpose of the scrapping tools is to create manifests suitable with
:ref:`intro_collector`.

.. Hint::
    Scrapping must be runned before running :ref:`intro_collector` else the scrapped
    information can not be collected.

Requirements
************

#. First you will need a `TMDb account <https://www.themoviedb.org/signup>`_;
#. Then `create an API key <https://www.themoviedb.org/settings/api>`_;
#. You will give this key to the command;


Giving API key to command
*************************

Either you give it directly as a string with option ``--key``: ::

    deovi COMMAND ... --key your-key

Or you can save your key into a file like ``tmdb-api-key.txt`` (and only the key,
nothing else) and give it with option ``--filekey``: ::

    deovi COMMAND ... --filekey tmdb-api-key.txt


.. _scrapping_tmdb_id:

TMDB Identifier
***************

Whatever the command you use, you will need to know the TMDB ID for the media to scrap,
it is the only way to find it with Deovi.

To get this identifier you will need first to browser `TMDb`_ site, find a media (TV or
Movie) and go to its details page. The ID is not very obvious, it is in the show details
page URL.

For example with the TV show *The Outer Limits*, its url should be: ::

    https://www.themoviedb.org/tv/21567-the-outer-limits

Where its ID is: ::

    21567


Manifest and cover files
************************

When using the ``scrap`` command you have to give a destination path which is a
directory dedicated to a single TV show. It needs to be dedicated since manifest and
cover files have a generic name that would overwrite any previous files from another
show.

So when the command succeed to retrieve a show details, you will possibly have these
files into the destination directory:

Manifest file
-------------

The manifest file contains details for a resource and will be updated from scrapper
with data returned by the TMDb API. This file can be used with :ref:`intro_collector`.

If a previous manifest file already existed in the destination directory it will be
totally overwritten by a new one. You should stick to the same format because this
command will not be able to manage format changes when overwriting and may forget
a previous manifest in different format.

Finally if there is any differences between old
and new manifest, they will be displayed and possibly stored into a
*Difference file* (see below).

Naming
......

Manifest file name is built depending the TMDB TYPE:

* TV has a generic filename ``manifest.[json,yaml]``;
* Movie adopt the same filename as its media source, such as for file ``foobar.mkv`` it
  will be ``foobar.[json.yaml]``;

.. Note::
    File name is only built for non existing manifest so this only apply when scrapping
    a single resource with command ``scrap``.

Format
......

The manifest format can be either YAML or JSON.

The minimal structure for a JSON manifest to be scrapped is: ::

    {
        "tmdb_id": 42,
        "tmdb_type": "tv"
    }

And in YAML it would be: ::

    tmdb_id: 42
    tmdb_type: tv

Where ``tmdb_id`` is the :ref:`scrapping_tmdb_id` and ``tmdb_type`` is the TMDB resource
type that can be either ``tv``, ``movie`` or ``collection``.

Only these attributes are required for the manifest to be scrapped, however the
``collection`` type is not scrapped.

Differences file
----------------

If there was already a manifest file in the destination directory, it will be
overwritten with the new one.

You can ask to store a resume of differences along the manifest file with option
``--write-diff``, it will contains something like this: ::

    Item root['ping'] removed from dictionary.
    Item root['genres'][2] removed from iterable.

This file is not really observed by the scrapper, you will need to remove it
yourself and it can be overwritten by a following run of the scrapper.

Difference file name is built from the manifest file name with suffix replaced to
``.diff.txt``.

Cover file
----------

If resource has a cover image, it will be downloaded and written along the manifest
file.

.. Warning::
    Previous existing cover file can be overwritten by a following run of the scrapper.

Cover file name is built from the manifest filename with suffix replaced with the cover
image format, commonly ``.jpg``.

Language
********

TMDb support many languages for details contents. You just have to give the right
language code to the command to get content in a specific language, obviously it must
be supported on TMDb.

.. Note::
    The details contents and cover image are affected by your language choice. However
    some contents may not be translated for some languages.

For example if you require to get details in english you would just have to ask for it
with option ``--language``: ::

    deovi scrap [TVID] [DESTINATION] --language en

The default language used in command is ``fr`` (french).


Usage
*****

Single resource from ID
-----------------------

We want to get the details from TV show *The Outer Limits* in english into
directory ``series/the-outer-limits``: ::

    deovi scrap tv 21567 ./series/the-outer-limits scrapped/ --language en

This would write the following files to given destination: ::

    scrapped/
    └── the-outer-limits/
        ├── cover.png
        └── manifest.yaml


Updating existing manifests
---------------------------

For many medias, instead of using ``scrap`` command for each of them, you can also
just use this command and point it to a directory path. The directory will be walked
recursively to find manifest files where to get the TMDB ID and TYPE to request for
scrapping.

Obviously this implies that all of your medias (TV or Movie) have their own manifest
file correctly filled with the TMDB ID and TYPE. So this command is more useful for
an already existing manifest structure to update.

For example this command will scrap information in english for all manifest found in the
directory ``./series/`` and update them in place: ::

    deovi manifescrap ./series/ --language en


Locking a manifest
------------------

You may sometime do not need to update some media details, for this you can edit the
manifest yourself to set the option ``locked`` to true. Then so the scrapper will ignore
the manifest, the first benefit of this is to avoid a request to TMDB.
