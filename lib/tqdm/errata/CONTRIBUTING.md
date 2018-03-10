HOW TO CONTRIBUTE TO TQDM
=========================

This file describes how to

- contribute changes to the project, and
- upload released to the pypi repository.

Most of the management commands have been directly placed inside the
Makefile:

```
make [<alias>]  # on UNIX-like environments
python setup.py make [<alias>]  # if make is unavailable
```

Use the alias `help` (or leave blank) to list all available aliases.


HOW TO COMMIT CONTRIBUTIONS
---------------------------

Contributions to the project are made using the "Fork & Pull" model. The
typical steps would be:

1. create an account on [github](https://github.com)
2. fork [tqdm](https://github.com/tqdm/tqdm)
3. make a local clone: `git clone https://github.com/your_account/tqdm.git`
4. make changes on the local copy
5. test (see below) and commit changes `git commit -a -m "my message"`
6. `push` to your github account: `git push origin`
7. create a Pull Request (PR) from your github fork
(go to your fork's webpage and click on "Pull Request."
You can then add a message to describe your proposal.)


TESTING
-------

To test functionality (such as before submitting a Pull
Request), there are a number of unit tests.

Standard unit tests
~~~~~~~~~~~~~~~~~~~

The standard way to run the tests:

- install `tox`
- `cd` to the root of the `tqdm` directory (in the same folder as this file)
- run the following command:

```
[python setup.py] make test
# or:
tox --skip-missing-interpreters
```

This will build the module and run the tests in a virtual environment.
Errors and coverage rates will be output to the console/log. (Ignore missing
interpreters errors - these are due to the local machine missing certain
versions of Python.)

Note: to install all versions of the Python interpreter that are specified
in [tox.ini](https://raw.githubusercontent.com/tqdm/tqdm/master/tox.ini),
you can use `MiniConda` to install a minimal setup. You must also make sure
that each distribution has an alias to call the Python interpreter:
`python27` for Python 2.7's interpreter, `python32` for Python 3.2's, etc.

Alternative unit tests with Nose
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Alternatively, use `nose` to run the tests just for the current Python version:

- install `nose` and `flake8`
- run the following command:

```
[python setup.py] make alltests
```



MANAGE A NEW RELEASE
=====================

This section is intended for the project's maintainers and describes
how to build and upload a new release. Once again,
`[python setup.py] make [<alias>]` will help.


SEMANTIC VERSIONING
-------------------

The tqdm repository managers should:

- regularly bump the version number in the file
[_version.py](https://raw.githubusercontent.com/tqdm/tqdm/master/tqdm/_version.py)
- follow the [Semantic Versioning](http://semver.org/) convention
- take care of this (instead of users) to avoid PR conflicts
solely due to the version file bumping

Note: tools can be used to automate this process, such as
[bumpversion](https://github.com/peritus/bumpversion) or
[python-semanticversion](https://github.com/rbarrois/python-semanticversion/).


CHECKING SETUP.PY
-----------------

To check that the `setup.py` file is compliant with PyPi requirements (e.g.
version number; reStructuredText in README.rst) use:

```
[python setup.py] make testsetup
```

To upload just metadata (including overwriting mistakenly uploaded metadata)
to PyPi, use:

```
[python setup.py] make pypimeta
```


MERGING PULL REQUESTS
---------------------

This section describes how to cleanly merge PRs.

1 Rebase
~~~~~~~~

From your project repository, merge and test
(replace `pr-branch-name` as appropriate):

```
git fetch origin
git checkout -b pr-branch-name origin/pr-branch-name
git rebase master
```

If there are conflicts:

```
git mergetool
git rebase --continue
```

2 Push
~~~~~~

Update branch with the rebased history:

```
git push origin pr-branch-name --force
```

Non maintainers can stop here.

Note: NEVER just `git push --force` (this will push all local branches,
overwriting remotes).

3 Merge
~~~~~~~

```
git checkout master
git merge --no-ff pr-branch-name
```

4 Test
~~~~~~

```
[python setup.py] make alltests
```

5 Version
~~~~~~~~~

Modify tqdm/_version.py and ammend the last (merge) commit:

```
git add tqdm/_version.py
git commit --amend  # Add "+ bump version" in the commit message
```

6 Push to master
~~~~~~~~~~~~~~~~

```
git push origin master
```


BUILDING A RELEASE AND UPLOADING TO PYPI
----------------------------------------

Formally publishing requires additional steps: testing and tagging.

Test
~~~~

- ensure that all online CI tests have passed
- check `setup.py` and `MANIFEST.in` - which define the packaging
process and info that will be uploaded to [pypi](pypi.python.org) -
using `[python setup.py] make installdev`

Tag
~~~

- ensure the version has been bumped, committed **and** tagged.
The tag format is `v{major}.{minor}.{patch}`, for example: `v4.4.1`.
The current commit's tag is used in the version checking process.
If the current commit is not tagged appropriately, the version will
display as `v{major}.{minor}.{patch}-{commit_hash}`.

Upload
~~~~~~

Build tqdm into a distributable python package:

```
[python setup.py] make build
```

This will generate several builds in the `dist/` folder. On non-windows
machines the windows `exe` installer may fail to build. This is normal.

Finally, upload everything to pypi. This can be done easily using the
[twine](https://github.com/pypa/twine) module:

```
[python setup.py] make pypi
```

Also, the new release can (should) be added to `github` by creating a new
release from the web interface; uploading packages from the `dist/` folder
created by `[python setup.py] make build`.

Notes
~~~~~

- you can also test on the pypi test servers `testpypi.python.org/pypi`
before the real deployment
- in case of a mistake, you can delete an uploaded release on pypi, but you
cannot re-upload another with the same version number
- in case of a mistake in the metadata on pypi (e.g. bad README),
updating just the metadata is possible: `[python setup.py] make pypimeta`


UPDATING GH-PAGES
-----------------

The most important file is README.rst, which sould always be kept up-to-date
and in sync with the in-line source documentation. This will affect all of the
following:

- The [main repository site](https://github.com/tqdm/tqdm) which automatically
  serves the latest README.rst as well as links to all of github's features.
  This is the preferred online referral link for tqdm.
- The [PyPi mirror](https://pypi.python.org/pypi/tqdm) which automatically
  serves the latest release built from README.rst as well as links to past
  releases.
- Many external web crawlers.


Additionally (less maintained), there exists:

- A [wiki](https://github.com/tqdm/tqdm/wiki) which is publicly editable.
- The [gh-pages project](https://tqdm.github.io/tqdm/) which is built from the
  [gh-pages branch](https://github.com/tqdm/tqdm/tree/gh-pages), which is
  built using [asv](https://github.com/spacetelescope/asv/).
- The [gh-pages root](https://tqdm.github.io/) which is built from a separate
  outdated [github.io repo](https://github.com/tqdm/tqdm.github.io).


QUICK DEV SUMMARY
-----------------

For expereinced devs, once happy with local master:

1. bump version in `tqdm/_version.py`
2. test (`[python setup.py] make alltests`)
3. `git commit [--amend]  # -m "bump version"`
4. `git push`
5. wait for tests to pass
    a) in case of failure, fix and go back to (2)
6. `git tag vM.m.p && git push --tags`
7. `[python setup.py] make distclean`
8. `[python setup.py] make build`
9. `[python setup.py] make pypi`
