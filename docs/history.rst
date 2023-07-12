.. _intro_history:

=======
History
=======

Version 0.6.0 - 2023/07/12
--------------------------

[scrap] Added a new command ``scrap`` which uses TMDb API to retrieve TV serie details
and write them to a manifest. The manifest is compatible with collector from
``collect`` command.


Version 0.5.2 - 2023/05/09
--------------------------

* [collect] Fixed dumped cover item filepath to be relative to the dump file;
* [collect] Fixed directory checksum to be done with cover source path, so no UUID is
  involved and the checksum is stable if directory has not changed;
* [rename] Fixed documentation for rename command;
* [rename] Fixed rename command help;


Version 0.5.1 - 2023/03/07
--------------------------

[collect] Added checksum feature to collector. Directory checksum is computed from the
directory payload as built from collector.


Version 0.5.0 - 2023/03/03
--------------------------

* [collect] Improved collector so it can retrieve extra informations from a YAML
  manifest and cover image for each directory;
* Improved ``setup.cfg`` to move extra requirements in specific sections so Tox is
  faster to install without unecessary requirements;


Version 0.4.1 - 2022/01/22
--------------------------

[collect] Fixed tests on collector which failed because of file datetimes which can
change from an installation to another. So we mocked up the method to get the formatted
datetime.


Version 0.4.0 - 2022/01/16
--------------------------

Added new command ``collect`` to recursively collect media file informations for a
given directory.


Version 0.3.1 - 2021/12/19
--------------------------

This is a release fix for release version. No code change have been done.


Version 0.3.0 - Unreleased
--------------------------

First working version.

* Finished refactoring;
* Finished test coverage;
* Finished new commandline with Click;
* Everything from old Python script have been implemented and tested.
* Added very few improvements on logging, job validation, task validation and output;
* Some tasks have been renamed compared to the old Python script;


Version 0.2.0 - Unreleased
--------------------------

Unworking version.

* Lots of refactoring;
* Starting test coverage;


Version 0.1.0 - Unreleased
--------------------------

First commit.

Unworking version.

This is a port of an old existing Python script so it can be packaged, correctly tested
and maintained.
