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

Writes system RPM configuration to a dump file and restore it.

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

``dnf debug-dump``

``--norepos``
    Do not dump content of enabled repos.

``dnf debug-restore``

``--output``
    Only output list of packages which will be installed or removed.
    No actuall changes are done.

``--install-latest``
    When installing use the latest package of the same name and architecture.

``--ignore-arch``
    When installing package ignore architecture and install missing packages
    matching the name, epoch, version and release.

``--filter-types=[install,remove,replace]``
    Limit package changes to specified type.
