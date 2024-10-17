================
DNF bootc Plugin
================

Manipulate image mode based systems using RPMs available from dnf repositories.

--------
Synopsis
--------

``dnf bootc [status|install] <options>``

-----------------
Arguments (bootc)
-----------------

``bootc status <options>``
    The status of the image mode system.

``bootc install [options] <pkg-spec>...``
    Install one or more packages.

``bootc remove [options] <pkg-spec>...``
    Remove one or more packages.

-------
Options
-------

All general DNF options are accepted, see `Options` in :manpage:`dnf(8)` for details.

``--json``
    Output JSON (valid on the status subcommand).

``--booted``
    Only print the booted deployment (valid on the status subcommand).

``--jsonpath EXPRESSION``
    Filter JSONPath expression (valid on the status subcommand).

``--pending-exit-77``
    If pending deployment available, exit 77 (valid on the status subcommand).

``--install PKG...``
    Overlay an additional package (valid on the remove subcommand).

``--uninstall PKG...``
    Remove overlayed additional package (valid on the install subcommand).

``--all``
    Remove all overlayed additional packages (valid on the remove subcommand).

``-A``, ``--apply-live``
    Apply changes to both pending deployment and running filesystem tree (valid on the install subcommand).

``--force-replacefiles``
    Allow package to replace files from other packages (valid on the install subcommand).

``-r``, ``--reboot``
    Initiate a reboot after operation is complete (valid on the install and remove subcommands).

``--allow-inactive``
    Allow inactive package requests (valid on the install and remove subcommands).

``--idempotent``
    Do nothing if package already (un)installed (valid on the install and remove subcommands).

``--unchanged-exit-77``
    If no overlays were changed, exit 77 (valid on the install and remove subcommands).

``--peer``
    Force a peer-to-peer connection instead of using the system message bus (valid on the status, install, and remove subcommands).
