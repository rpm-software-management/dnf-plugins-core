================
Download Plugin
================

Download binary or source packages.

Synopsis
--------

``dnf download [options] <pkg-spec> ..``

Arguments
----------

``<pkg-spec>``
    Package specification for the package to download (Same package specification as for other dnf commands).

Options
---------

``--help-cmd``
    Show this help.

``--source``
    Download the source rpm.

``--destdir``
    Download directory, default is the current directory (the directory must exist).

``--resolve``
    Resolve and download dependencies, not installed on the local system.

Examples
--------
``dnf download dnf``
    Download the latest dnf package to the current directory.

``dnf download dnf --destdir /tmp/dnl``
    Download the latest dnf package to the /tmp/dnl directory (the directory must exist).

``dnf download dnf --source``
    Download the latest dnf source package to the current directory.

``dnf download btanks --resolve``
    Download the latest btanks package and the uninstalled dependencies to the current directory.


