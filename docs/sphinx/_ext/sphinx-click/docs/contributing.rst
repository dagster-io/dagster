Contribution
============

We welcome all contributions to `sphinx-click`.

Support
-------

Open and issue in the `issue tracker`_ for all support requests.
`StackOverflow`_ is also worth considering.

Reporting Issues
----------------

Report all issues in the `issue tracker`_. When doing so, please include
version information for:

- Python
- `click`
- `sphinx-click`

Submitting Patches
------------------

All patches should be submitted as pull requests on the `GitHub project`_.

- Include tests if fixing a bug

- Clearly explain what you're trying to accomplish

- Follow :pep:`8`. You can use the `pep8` tox target for this

Testing
-------

`sphinx-click` uses `tox` and `unittest` for testing. To run all tests, run:

.. code-block:: shell

    $ tox

We support a number of Python versions. To list available environments, run:

.. code-block:: shell

    $ tox --list

To run one of these environments, such as `py27` which runs tests under Python
2.7, run:

.. code-block:: shell

    $ tox -e py27

.. _issue tracker: https://github.com/click-contrib/sphinx-click/issues
.. _StackOverflow: https://stackoverflow.com
.. _GitHub project: https://github.com/click-contrib/sphinx-click
