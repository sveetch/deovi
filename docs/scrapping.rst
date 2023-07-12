.. _TMDb: https://www.themoviedb.org/
.. _TMDb API: https://developer.themoviedb.org/docs/getting-started

.. _intro_scrapping:

=========
Scrapping
=========

.. Note::
    To use this command you will have to install Deovi with the feature ``scrapping``.

The scrapping tool stands on `TMDb API`_ to get TV serie details and cover. Details
are written to manifest along the cover into the given destination.

The first purpose of this scrapping tool is to create manifest suitable with collector
from ``collect``.

Requirements
************

#. First you will need a `TMDb account <https://www.themoviedb.org/signup>`_;
#. Then `create an API key <https://www.themoviedb.org/settings/api>`_;
#. You will give this key to the command else it won't be able to request the
   `TMDb API`_;

Giving API key to command
*************************

Either you give it directly as a string with option ``--key``: ::

    deovi scrap [TVID] [DESTINATION] --key your-key

Or you can save your key into a file like ``tmdb-api-key.txt`` (and only the key,
nothing else) and give it with option ``--filekey``: ::

    deovi scrap [TVID] [DESTINATION] --filekey tmdb-api-key.txt

TV Id
*****

Actually only TV serie shows are implemented for scrapping. When you need to request
for a show details you will have to give its ID since Deovi does not implement show
discovering from a title or any other field.

So to get this ID you will need first to browser `TMDb`_ site, find a show and go
to its details page. The ID is not very obvious, it is in the show details page URL.

For example with the show *The Outer Limits*, its url should be: ::

    https://www.themoviedb.org/tv/21567-the-outer-limits

Where its ID is: ::

    21567

Manifest and poster files
*************************

When using the ``scrap`` command you have to give a destination path which is a
directory dedicated to a single TV show. It needs to be dedicated since manifest and
poster files have a generic name that would overwrite any previous files from another
show.

So when the command succeed to retrieve a show details, you will possibly have these
files into the destination directory:

manifest.yaml
    The manifest file in YAML format which will contains all details returned by the
    TMDb API and is suitable with collector from ``collect`` command.

    If a previous manifest file already existed in the destination directory it will be
    totally overwritten by a new one. However if there is any differences between old
    and new manifest, they will be showed and possibly stored into a
    ``manifest.diff.txt`` (see below).

manifest.diff.txt
    If there was already a manifest file in the destination directory, it will be
    overwritten with the new one.

    You can ask to store a resume of differences along the manifest file with option
    ``--write-diff``, it will contains something like this: ::

        Item root['ping'] removed from dictionary.
        Item root['genres'][2] removed from iterable.

    This file is not really observed by the scrapper, you will need to remove it
    yourself and it can be overwritten by a following run of the scrapper.

cover.jpg
    If show has a poster image, it will be downloaded and written with this name.

    Previous existing cover file can be overwritten by a following run of the scrapper.


Language
********

TMDb support many languages for details contents. You just have to give the right
language code to the command to get content in a specific language, obviously it must
be supported on TMDb.

.. Note::
    The details contents and poster image are affected by your language choice.

For example if you require to get details in french you would just have to ask for it
with option ``--language``: ::

    deovi scrap [TVID] [DESTINATION] --language fr

The default language used in command is "english", so you don't need to ask for it
explicitely.


Usage
*****

For example, we want to get the details from TV show *The Outer Limits* in french into
directory ``scrapped/the-outer-limits``: ::

    deovi scrap 21567 ./scrapped/the-outer-limits --language fr

That would write the following files to given destination: ::

    the-outer-limits/
    ├── cover.png
    └── manifest.yaml

