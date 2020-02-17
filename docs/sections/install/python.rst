Installing Python and pip
-------------------------

.. toctree::
  :hidden:

To check that Python and the pip package manager are already installed in your environment, you
can run:

.. code-block:: console

    $ python --version
    $ pip --version

If you're running Python 3.3 or later, you already have the venv package for managing
virtualenvs. On Python 2.7, you can check whether you have the virtualenv tool installed by
running:

.. code-block:: console

    $ virtualenv --version

If these tools aren't present on your system, you can install them as follows:

.. rubric:: Installing Python on Ubuntu

.. code-block:: console

    $ sudo apt update
    $ sudo apt install python3-dev python3-pip

This will install Python 3 and pip on your system.

.. rubric:: Installing Python on macOS

Using `Homebrew <https://brew.sh/>`_:

.. code-block:: console

    $ brew update
    $ brew install python  # Python 3

This will install Python 3 on your system.

If you are using the macOS-provided Python 2.7, you can install virtualenv with:

.. code-block:: console

    $ sudo pip install -U virtualenv  # system-wide install

.. rubric:: Installing Python on Windows

- Install the *Microsoft Visual C++ 2015 Redistributable Update 3*. This comes with *Visual Studio 2015* but can be installed separately as follows:

  1. Go to the Visual Studio downloads,
  2. Select *Redistributables and Build Tools*,
  3. Download and install the *Microsoft Visual C++ 2015 Redistributable Update 3*.

- Install the 64-bit Python 3 release for Windows (select ``pip`` as an optional feature).

To use the ``dagit`` tool, you will also need to
`install yarn <https://yarnpkg.com/lang/en/docs/install/>`_.



.. rubric:: Notes on Python virtualenvs

We strongly recommend installing dagster inside a Python virtualenv.

If you are running Anaconda, you should install dagster inside a Conda environment.

To create a virtual environment on Python 3, you can just run:

.. code-block:: console

    $ python3 -m venv ~/.venvs/dagster

This will create a new Python environment whose interpreter and libraries
are isolated from those installed in other virtual environments, and
(by default) any libraries installed in a “system” Python installed as part
of your operating system.

On Python 2, you can use a tool like
`virtualenvwrapper <https://virtualenvwrapper.readthedocs.io/en/latest/>`_
to manage your virtual environments, or just run:

.. code-block:: console

    $ virtualenv ~/.venvs/dagster

You'll then need to 'activate' the virtualenvironment, in bash by
running:

.. code-block:: console

    $ source ~/.venvs/dagster/bin/activate

(For other shells, see the
`venv documentation <https://docs.python.org/3/library/venv.html#creating-virtual-environments>`_.)

If you are using Anaconda, you can run:

.. code-block:: console

    $ conda create --name dagster

And then, on macOS or Ubuntu:

.. code-block:: console

    $ source activate dagster

Or, on Windows:

.. code-block:: console

    $ activate dagster
