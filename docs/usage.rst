.. _intro_usage:

=====
Usage
=====

-----

Every task must be run from a Job file. A job file is dedicated to work on a specific
directory called the **basepath**.

Create a new Job
----------------

You can quickly create a new empty Job file configured for a basepath.

::

    deovi job /home/foo/bar

::

    deovi job /home/foo/bar --destination /home/foo/plop/plip.json

Run jobs
--------

You can run a single job: ::

    deovi rename foo.json

Or multiple ones: ::

    deovi rename foo.json bar.json /home/foo/plop/plip.json

Help
----

There is the base tool help: ::

    deovi -h

And then each tool command has its own help: ::

    deovi rename -h
