================
DNF bootc Plugin
================

Manipulate image mode based systems using RPMs available from dnf repositories.

--------
Synopsis
--------

``dnf bootc [status] <options>``

-----------------
Arguments (bootc)
-----------------

``bootc status <options>``
    The status of the image mode system.

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
    If pending deploymewnt available, exit 77 (valid on the status subcommand).

``--peer``
    Force a peer-to-peer connection instead of using the system message bus (valid on the status subcommand).
