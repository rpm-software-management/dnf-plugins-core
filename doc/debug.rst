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

================
DNF debug Plugin
================

-----------
Description
-----------

The plugin provides two dnf commands:

``debug-dump``
    Writes system RPM configuration to a dump file

``debug-restore``
    Restore the installed packages to the versions written in the dump file. By
    default, it does not remove already installed versions of install-only
    packages and only marks those versions that are mentioned in the dump file
    for installation. The final decision on which versions to keep on the
    system is left to dnf and can be fine-tuned using the `installonly_limit`
    (see :manpage:`dnf.conf(5)`) configuration option.

.. note:: DNF and Yum debug files are not compatible and thus can't be used
          by the other program.

--------
Synopsis
--------

``dnf debug-dump [--norepos] [<filename>]``

``dnf debug-restore [--output] [--install-latest] [--ignore-arch]
[--filter-types = [install,remove,replace]] <filename>``

---------
Arguments
---------

``<filename>``
    File to write dump to or read from.

-------
Options
-------

All general DNF options are accepted, see `Options` in :manpage:`dnf(8)` for details.

``dnf debug-dump``

``--norepos``
    Do not dump content of enabled repos.

``dnf debug-restore``

``--filter-types=[install,remove,replace]``
    Limit package changes to specified type.

``--ignore-arch``
    When installing package ignore architecture and install missing packages
    matching the name, epoch, version and release.

``--install-latest``
    When installing use the latest package of the same name and architecture.

``--output``
    Only output list of packages which will be installed or removed.
    No actuall changes are done.

``--remove-installonly``
    Allow removal of install-only packages. Using this option may result in an
    attempt to remove the running kernel version (in situations when the currently
    running kernel version is not part of the dump file).
