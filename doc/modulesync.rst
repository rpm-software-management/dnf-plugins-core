..
  Copyright (C) 2015  Red Hat, Inc.

  This copyrighted material is made available to anyone wishing to use,
  modify, copy, or redistribute it subject to the terms and conditions of
  the GNU General Public License v.2, or (at your option) any later version.
  This program is distributed in the hope that it will be useful, but WITHOUT
  ANY WARRANTY expressed or implied, including the implied warranties of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
  Public License for more details.  You should have received a copy of the
  GNU General Public License along with this program; if not, write to the
  Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
  02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
  source code or documentation are not subject to the GNU General Public
  License and may only be used or replicated with the express permission of
  Red Hat, Inc.

====================
DNF modulesync Plugin
====================

Download packages from modules and/or create a repository with modular data.

--------
Synopsis
--------

``dnf modulesync [options] [<module-spec>...]``

-----------
Description
-----------

`modulesync` downloads packages from modules according to provided arguments and creates a repository with modular data
in working directory. In environment with modules it is recommend to use the command for redistribution of packages,
because DNF does not allow installation of modular packages without modular metadata on the system (Fail-safe
mechanism). The command without an argument creates a repository like `createrepo_c` but with modular metadata collected
from all available repositories.

See examples.

---------
Arguments
---------

``<module-spec>``
    Module specification for the package to download. The argument is an optional.

-------
Options
-------

All general DNF options are accepted. Namely, the ``--destdir`` option can be used to specify directory where packages
will be downloaded and the new repository created. See `Options` in :manpage:`dnf(8)` for details.


``-n, --newest-only``
    Download only packages from the newest modules.

``--enable_source_repos``
    Enable repositories with source packages

``--enable_debug_repos``
    Enable repositories with debug-info and debug-source packages

``--resolve``
    Resolve and download needed dependencies

--------
Examples
--------

``dnf modulesync nodejs``
    Download packages from `nodejs` module and crete a repository with modular metadata in working directory

``dnf download nodejs``

``dnf modulesync``
    The first `download` command downloads nodejs package into working directory. In environment with modules `nodejs`
    package can be a modular package therefore when I create a repository I have to insert also modular metadata
    from available repositories to ensure 100% functionality. Instead of `createrepo_c` use `dnf modulesync`
    to create a repository in working directory with nodejs package and modular metadata.

``dnf --destdir=/tmp/my-temp modulesync nodejs:14/minimal --resolve``
    Download package required for installation of `minimal` profile from module `nodejs` and stream `14` into directory
    `/tmp/my-temp` and all required dependencies. Then it will create a repository in `/tmp/my-temp` directory with
    previously downloaded packages and modular metadata from all available repositories.

``dnf module install nodejs:14/minimal --downloadonly --destdir=/tmp/my-temp``

``dnf modulesync --destdir=/tmp/my-temp``
    The first `dnf module install` command downloads package from required for installation of `minimal` profile from module
    `nodejs` and stream `14` into directory `/tmp/my-temp`. The second command `dnf modulesync` will create
    a repository in `/tmp/my-temp` directory with previously downloaded packages and modular metadata from all
    available repositories. In comparison to `dnf --destdir=/tmp/my-temp modulesync nodejs:14/minimal --resolve` it will
    only download packages required for installation on current system.


--------
See Also
--------

* :manpage:`dnf(8)`, DNF Command Reference
