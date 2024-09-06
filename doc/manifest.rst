====================
 DNF manifest Plugin
====================

Working with RPM package manifest files using the ``libpkgmanifest`` library.

:ref:`Strict <strict-label>` mode is enforced for all operations.

--------
Synopsis
--------

``dnf manifest new [options] [<package-name-spec>...]``

``dnf manifest download [options]``

``dnf manifest install [options]``

-----------
Subcommands
-----------

``new``
    Generate a new manifest file based on the provided package specs.

    The specs are resolved, and all packages and their dependencies
    are recorder in the manifest file, considering the current system
    state and dnf configuration.

    If no specs are provided, the manifest is generated from the
    installed packages on the system.

``download``
    Download all packages specified in the manifest file to disk.

    By default, packages are downloaded to a subfolder named after the 
    manifest file. You can also use the global ``--destdir`` option to
    specify a custom directory for the downloaded packages.

``install``
    Install all packages specified in the manifest file.

---------
Arguments
---------

``<package-name-spec>``
    Specification for including a package in the manifest file.
    Local RPMs or filenames are not supported.
    For more information, refer to :ref:`Specifying Packages <specifying_packages-label>`.

-------
Options
-------

``--file``
    Specify a custom path for the manifest file.
    By default, ``packages.manifest.yaml`` is used.

``--source``
    Include source packages in consideration.
    Not supported for the ``install`` command.

``--url-only``
    Use package URLs from the manifest instead of resolving packages from repositories.
    Repository metadata is not loaded for this operation.
    Applicable only for the ``download`` command.

--------
Examples
--------

``dnf manifest new alsa-lib alsa-tools``
    Create a new manifest file at the default ``packages.manifest.yaml`` location,
    containing the ``alsa-lib`` and ``alsa-tools`` packages along with all their dependencies.

``dnf manifest download --file /home/user/Downloads/manifest.yaml --source``
    Download all packages, including source packages, specified in the given manifest file.

``dnf manifest install -y``
    Install all packages specified in the manifest file located in the current directory
    under the default file name, automatically answering "yes" to all prompts during the
    transaction resolution.

--------
See Also
--------

* `libpkgmanifest upstream <https://github.com/rpm-software-management/libpkgmanifest>`_
