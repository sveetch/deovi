.. _intro_history:

=======
History
=======

Version 1.0.0 - 2026/08/16
**************************

This is a large refactoring of the Deovi core and commands to improve code and add new
features.

The refactoring is too heavy to be described here so you would need
to search through commits to find details, however for command usage there is almost
not breaking changes except the ones listed below.

* Added support for Python 3.12 and 3.13;
* Removed support for Python 3.8 and 3.9;
* Updated Makefile;
* Updated package setup for a minimal version of all requirements;
* Fixed tests failing because of minor change on information of sample tv serie
  *The Outer Limits* from TMDb;
* Added logo;
* Moved documentation theme to "Furo";
* Scrapping requirements (deepdiff, tmdbv3api and requests) are not optional anymore
  and are now part of the base package requirements;
* [collect] Because of some changes in collector and scrapper behaviors, the resulting
  registry dump has some little changes:

  * tmdb id, tmdb type, cover and title fields have moved into the manifest fields;
  * Now the dump can contain manifest for Media files;
  * 'DirectoryInformation.children_files' attribute has been renamed to
    'DirectoryInformation.medias';
  * 'MediaInformation.directory' attribute has been renamed to
    'MediaInformation.dir_altname';
  * The dump registry include now a new field 'deovi' which contains the Deovi version
    used to create dump and also a date of creation;

* [collect] Update documentation;
* [scrap] Improved Scrapper class and 'scrap' command to support movie in addition to
  tv resource;
* [scrap] Improved Scrapper to output manifest in JSON format in addition to YAML;
* [scrap] Scrapper now support the ``locked`` option from a manifest to avoid update;
* [scrap] Breaking change: The command now required the TMDB type to be given as the
  first argument;
* [scrap] Added original language, casting and crew to retrieved information from
  payload;
* [scrap] Added new command 'manifescrap' command to recursively search for manifest of
  resources to scrap;
* [scrap] Now the scrapper methods for many resources (either from manifest objects or
  recursive path) process resource per chunk and apply a pause between them to follow
  the soft request limit from TMDB API;
* [scrap] Update documentation;


Version 0.7.0 - 2024/04/28
**************************

* [collect] Breaking changes: The collection dump structure has changed to include
  device statistics in item ``device`` and all collected directory items (previously at
  root) have been moved into item ``registry``;
* [collect] Fixed inconsistant collector test because of arbitrary order from
  ``Path.iterdir()``;


Version 0.6.1 - 2023/07/16
**************************

* [collect] ``AssetStorage.store_assets()`` now returns also the asset storage
  directory along stored asset filepath list in a tuple;
* [scrap] Added dry mode so everything is running but nothing is written or removed
  from filesystem;


Version 0.6.0 - 2023/07/12
**************************

[scrap] Added a new command ``scrap`` which uses TMDb API to retrieve TV serie details
and write them to a manifest. The manifest is compatible with collector from
``collect`` command.


Version 0.5.2 - 2023/05/09
**************************

* [collect] Fixed dumped cover item filepath to be relative to the dump file;
* [collect] Fixed directory checksum to be done with cover source path, so no UUID is
  involved and the checksum is stable if directory has not changed;
* [rename] Fixed documentation for rename command;
* [rename] Fixed rename command help;


Version 0.5.1 - 2023/03/07
**************************

[collect] Added checksum feature to collector. Directory checksum is computed from the
directory payload as built from collector.


Version 0.5.0 - 2023/03/03
**************************

* [collect] Improved collector so it can retrieve extra informations from a YAML
  manifest and cover image for each directory;
* Improved ``setup.cfg`` to move extra requirements in specific sections so Tox is
  faster to install without unecessary requirements;


Version 0.4.1 - 2022/01/22
**************************

[collect] Fixed tests on collector which failed because of file datetimes which can
change from an installation to another. So we mocked up the method to get the formatted
datetime.


Version 0.4.0 - 2022/01/16
**************************

Added new command ``collect`` to recursively collect media file informations for a
given directory.


Version 0.3.1 - 2021/12/19
**************************

This is a release fix for release version. No code change have been done.


Version 0.3.0 - Unreleased
**************************

First working version.

* Finished refactoring;
* Finished test coverage;
* Finished new commandline with Click;
* Everything from old Python script have been implemented and tested.
* Added very few improvements on logging, job validation, task validation and output;
* Some tasks have been renamed compared to the old Python script;


Version 0.2.0 - Unreleased
**************************

Unworking version.

* Lots of refactoring;
* Starting test coverage;


Version 0.1.0 - Unreleased
**************************

First commit.

Unworking version.

This is a port of an old existing Python script so it can be packaged, correctly tested
and maintained.
