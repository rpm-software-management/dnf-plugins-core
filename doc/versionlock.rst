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

======================
DNF versionlock Plugin
======================

-----------
Description
-----------

`versionlock` is a plugin that takes a set of names and versions for packages and
excludes all other versions of those packages. This allows you to protect
packages from being updated by newer versions. Alternately, it accepts a specific
package version to exclude from updates, e.g. for when it's necessary to skip a
specific release of a package that has known issues.

The plugin provides a command `versionlock` which allows you to view and edit the
list of locked packages easily.

The plugin will walk each line of the versionlock file, and parse out the name and
version of the package. It will then exclude any package by that name that
doesn't match one of the versions listed within the file. This is basically
the same as using `dnf --exclude` for the package name itself (as you cannot exclude
installed packages), but dnf will still see the versions you have
installed/versionlocked as available so that `dnf reinstall` will still
work, etc.

It can also work in the opposite way, like a fast exclude, by prefixing a '!'
character to the version recorded in the lock list file. This specifically
excludes a package that matches the version exactly.

Note the versionlock plugin does not apply any excludes in non-transactional
operations like `repoquery`, `list`, `info`, etc.

Note that the versionlock plugin only applies to in-repository packages.
Packages passed on the DNF command line as local files won't be affected.

--------
Synopsis
--------

``dnf versionlock [options] [add|exclude|list|delete|clear] [<package-name-spec>]``

---------
Arguments
---------

``<package-name-spec>``
    Package spec to lock or exclude.

-----------
Subcommands
-----------

``dnf versionlock add <package-name-spec>``
    Add a versionlock for all available packages matching the spec. It means that only versions of
    packages represented by ``<package-name-spec>`` will be available for transaction operations.
    Each ``<package-name-spec>`` is converted to concrete NEVRAs which are used for locking. The NEVRAs to lock to are first searched among installed packages and then (if none is found) in all currently available packages.

    Examples::

        Locking a package to the version installed:

            $ dnf repoquery --installed bash
            bash-0:5.0.7-1.fc30.x86_64

            $ dnf repoquery bash
            bash-0:5.0.2-1.fc30.i686
            bash-0:5.0.2-1.fc30.x86_64
            bash-0:5.0.7-1.fc30.i686
            bash-0:5.0.7-1.fc30.x86_64

            $ dnf versionlock add bash
            Adding versionlock on: bash-0:5.0.7-1.fc30.*

        Locking not installed package to any of available versions:

            $ dnf repoquery --installed mutt

            $ dnf repoquery mutt
            mutt-5:1.11.4-1.fc30.x86_64
            mutt-5:1.12.1-3.fc30.x86_64

            $ dnf versionlock add mutt
            Adding versionlock on: mutt-5:1.11.4-1.fc30.*
            Adding versionlock on: mutt-5:1.12.1-3.fc30.*

    .. note:: Be careful when adding specific versions

        If you add a package specifying a version with ``dnf versionlock mutt-5:1.11.4-1.fc30.x86_64`` then, if you run ``dnf versionlock add mutt``
        versionlock will not add ``mutt-5:1.12.1-3.fc30.x86_64``.

``dnf versionlock exclude <package-name-spec>``
    Add an exclude (within  versionlock) for the available packages matching the spec. It means that
    packages represented by ``<package-name-spec>`` will be excluded from transaction operations.

``dnf versionlock list`` or ``dnf versionlock``
    List the current versionlock entries.

``dnf versionlock delete <package-name-spec>``
    Remove any matching versionlock entries.

``dnf versionlock clear``
    Remove all versionlock entries.

-------
Options
-------

All general DNF options are accepted, see `Options` in :manpage:`dnf(8)` for details.

``--raw``
    Do not resolve ``<package-name-spec>`` to NEVRAs to find specific version to lock to. Instead ``<package-name-spec>`` are used as they are. This enables locking to not yet available versions of the package.
    For example you may want to keep the `bash` package on major version 5 and consume any future updates as far as they keep the major version::

        $ dnf versionlock add --raw 'bash-5.*'
        Adding versionlock on: bash-5.*

-------------
Configuration
-------------

``/etc/dnf/plugins/versionlock.conf``

The minimal content of conf file should contain ``main`` sections with ``enabled`` and
``locklist`` parameters.


``locklist``
      This option is a string that points to the file which has the versionlock
      information in it. Note that the file has to exist (or the versionlock plugin
      will make dnf exit). However, it can be empty.

      The file takes entries in the format of ``<package-name-spec>`` (optionally prefixed with '!' for
      excludes).
      See `Specifying packages` in :manpage:`dnf(8)` for details.

-----
Notes
-----

A specified package does not have to exist within the available cache of repository data
to be considered valid for locking or exclusion. This is by design, to accommodate use
cases such as a presently disabled repository. However, a package must exist in the
repository cache when the ``add`` or ``exclude`` subcommands are invoked for it.
