.. _intro_usage:

=====
Usage
=====

Principle is to run tasks from a Job to rename files from a directory (not recursively).

Job
***

Job file is what defines the ``basepath`` to search for file to rename, some options
and renaming tasks.

It should be something like this: ::

    {
        "name": "A totally optional name",
        "basepath": "/home/foo/",
        "reversed": false,
        "extensions": ["avi", "mp4", "mkv"],
        "tasks": [
            [
                "lowercase",
                {}
            ],
            [
                "add_prefix",
                {
                    "prefix": "Foobar_"
                }
            ]
        ]
    }

As you can see, this is JSON format. For this sample, we use two tasks.

Tasks are described in next section but for the Job context, you need to know that
tasks are proceeded in the same order as described.

The job will execute the succession of tasks on each file and return the new final
filename after the last task.

Job options
-----------

**name**
    Optional name, you can set it to ``null``. It is not used or displayed
    anywhere because this is just a description for your needs;
**basepath**
    The directory path where the Job will search for file to rename. It can
    be a relative path which will be resolved to your current directory and it must be
    an existing and valid directory.
**reversed**
    Set it to ``true`` to reverse the file listing if needed, else let it to ``False``.
**extensions**
    A list of file extensions to filter file listing, if set only the files which end
    with one of enabled extension will be renamed, other ones will be ignored. Set its
    value to ``null`` accept any file extensions.
**tasks**
    A list of tasks and their options to execute on a file. This is an error to have
    an empty list of tasks.


Task
****

A task doesn't make smart assumptions on filename. It is only aware of the current
file path and its position in the file listing.

A task is just some string manipulation on the filename, although aware of the file
path, it is only to modify the file name (including extension). Some task are done
to never change the file extension and some others can change it.


Available tasks
---------------

These are the task rules you can add to your Job ``tasks`` option. You can add as many
tasks as you want. Just remember than each task starts from the previous task returns,
or the original filename for the very first task in list.

capitalize
..........

Capitalize file name.

Scope
    File name and extension.
Options
    None.
Rule
    ::

        [
            "capitalize",
            {}
        ]
Sample
    ``HOME_foo.MP4`` will be converted to ``Home_foo.mp4``.


lowercase
.........

Lowercase file name, work on the whole filename including extension.

Scope
    File name and extension.
Options
    None.
Rule
    ::

        [
            "lowercase",
            {}
        ]
Sample
    ``HOME_foo.MP4`` will be converted to ``home_foo.mp4``.


uppercase
.........

Uppercase file name.

Scope
    File name and extension.
Options
    None.
Rule
    ::

        [
            "uppercase",
            {}
        ]
Sample
    ``HOME_foo.mp4`` will be converted to ``HOME_FOO.MP4``.


underscore_to_dash
..................

Convert some strings into another ones:

* ``_`` to ``-``;
* ``---`` to ``_``;

Scope
    File name and extension.
Options
    None.
Rule
    ::

        [
            "underscore_to_dash",
            {}
        ]
Sample
    ``ping_-_foo_bar.mp4`` will be converted to ``ping_foo-bar.mp4``.


add_prefix
..........

Add a prefix before filename.

Works on the whole filename including extension.

Scope
    File name only.
Options
    ``prefix`` is a required string for the value to add.
Rule
    ::

        [
            "add_prefix",
            {
                "prefix": STRING*
            }
        ]
Sample
    With prefix option value to ``Plop_`` the source string ``foo-bar.mp4`` will be
    converted to ``Plop_foo-bar.mp4``.


numerate
........

Prefix file name with a string of index position padded with zero.

Scope
    File name only.
Options
    * ``zfill`` is a required integer. It defines padding length to fill;
    * ``start`` is an optional integer. It defines a number to add to the current
      file position. Default to zero;
    * ``divider`` is an optional string. If not empty, this string will be used between
      computed position string and filename. Default to ``_``;
Rule
    ::

        [
            "numerate",
            {
                "zfill": INTEGER*,
                "start": INTEGER,
                "divider": STRING
            }
        ]
Sample
    With options ``zfill`` set to ``2``. For a list of files ``Foo.txt``, ``Bar.txt``
    and ``Ping.txt``.

    Filenames would result to ``01_Foo.txt``, ``02_Bar.txt`` and ``03_Ping.txt``.

    For the same files and configuration with ``start`` set to ``8`` this would results
    to ``09_Foo.txt``, ``10_Bar.txt`` and ``11_Ping.txt``.


catch_segments
..............

Divide filename from given divider string and join resulting segments according to
options.

Scope
    File name only.
Options
    * ``divider`` is a required string. The filename will be splitted on this string;
    * ``slice_start`` is a required integer. It defines the first segment to start,
      previous segments will be ignored. The segment list is indexed on zero;
    * ``slice_end`` is an optional integer. It defines the last segment to keep.
      Default is empty so every segments from start will be keeped. Note this is based
      on the Python list slicing end, it may not work as you could expect it;
    * ``joiner`` is an optional string. This string will be used to join segments.
      Default to ``-``;
Rule
    ::

        [
            "catch_segments",
            {
                "divider": STRING*,
                "slice_start": INTEGER*,
                "slice_end": INTEGER,
                "joiner": STRING
            }
        ]
Sample
    For source string ``One.two.three.four.five.six.txt``. With options ``divider`` set
    to ``.``, ``slice_start`` set to ``0``, ``slice_end`` set to ``3`` and ``joiner``
    set to ``-``.

    The result will be ``One-two-three.txt``.

    For the same source and configuration with ``slice_start`` set to ``2`` and
    ``slice_end`` set to ``3``, the result will be ``three.txt``.

replace
.......

Replace every occurences of a string in filename by another one.

Scope
    File name and extension.
Options
    * ``from`` required string to replace;
    * ``to`` required string to add in place of ``from`` occurences;
Rule
    ::

        [
            "replace",
            {
                "from": STRING*,
                "to": STRING*
            }
        ]
Sample
    For source string ``Foo-bar_Plip-bar-plop.txt``. With options ``from`` set
    to ``-bar`` and ``to`` set to ``_ping``.

    The result will be ``Foo_ping_Plip_ping-plop.txt``.


Create a new Job
****************

You can quickly create a new empty Job file configured for a basepath.

::

    deovi job /home/foo/bar

Which will creates file ``bar.json`` at current directory.

Or with a specific destination path::

    deovi job /home/foo/bar --destination /home/foo/plop/plip.json

Which will creates file ``/home/foo/plop/plip.json``.

Once create, the Job file is almost empty with default values for required options and
no tasks, just the ``basepath`` is configured for given basepath directory.


Run jobs
********

You can run a single job: ::

    deovi rename foo.json

Or multiple ones: ::

    deovi rename foo.json bar.json /home/foo/plop/plip.json

Help
****

There is the base tool help: ::

    deovi -h

And then each tool command has its own help: ::

    deovi rename -h
