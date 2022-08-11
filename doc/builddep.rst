===================
DNF builddep Plugin
===================

Install whatever is needed to build the given .src.rpm, .nosrc.rpm or .spec file.

.. warning:: Build dependencies in a package (i.e. src.rpm) might be different
             than you would expect because they were evaluated according macros
             set on the package build host.

--------
Synopsis
--------

``dnf builddep <package>...``

---------
Arguments
---------

``<package>``
    Either path to .src.rpm, .nosrc.rpm or .spec file or package available in a repository.

-------
Options
-------

All general DNF options are accepted, see `Options` in :manpage:`dnf(8)` for details.

``--help-cmd``
    Show this help.

``-D <macro expr>, --define <macro expr>``
    Define the RPM macro named `macro` to the value `expr` when parsing spec files. Does not apply for source rpm files.

``--spec``
    Treat arguments as .spec files.

``--srpm``
    Treat arguments as source rpm files.

``--skip-unavailable``
    Skip build dependencies not available in repositories. All available build dependencies will be installed.

Note that `builddep` command does not honor the `--skip-broken` option, so there is no way to skip uninstallable packages (e.g. with broken dependencies).

--------
Examples
--------

``dnf builddep foobar.spec``
    Install the needed build requirements, defined in the foobar.spec file.

``dnf builddep --spec foobar.spec.in``
    Install the needed build requirements, defined in the spec file when filename ends
    with something different than ``.spec``.

``dnf builddep foobar-1.0-1.src.rpm``
    Install the needed build requirements, defined in the foobar-1.0-1.src.rpm file.

``dnf builddep foobar-1.0-1``
    Look up foobar-1.0-1 in enabled repositories and install build requirements
    for its source rpm.

``dnf builddep -D 'scl python27' python-foobar.spec``
    Install the needed build requirements for the python27 SCL version of python-foobar.
