.. _Python: https://www.python.org/
.. _Click: https://click.palletsprojects.com
.. _Python Slugify: https://github.com/un33k/python-slugify
.. _Unidecode: https://github.com/avian2/unidecode/tree/master/unidecode
.. _PyYAML: https://github.com/yaml/pyyaml/
.. _deepdiff: https://github.com/seperman/deepdiff
.. _tmdbv3api: https://github.com/AnthonyBloomer/tmdbv3api
.. _requests: https://requests.readthedocs.io/en/latest/

=====
Deovi
=====

Tools to rename files, collect their filepaths and scrap information from TMDB.

Links
*****

* Read the documentation on `Read the docs <https://deovi.readthedocs.io/>`_;
* Download its `PyPi package <https://pypi.python.org/pypi/deovi>`_;
* Clone it on its `Github repository <https://github.com/sveetch/deovi>`_;

Dependencies
************

* `Python`_ >=3.10;
* `Click`_ >=8.0;
* `Python Slugify`_ >=5.0.0;
* `Unidecode`_ (as a sub dependency from "Python Slugify");
* `PyYAML`_ >=6.0;

And optional dependancies when ``scrapping`` feature is enabled:

* `deepdiff`_;
* `tmdbv3api`_ ==1.7.7;
* `requests`_;
