..
  Copyright (C) 2018 Red Hat, Inc.

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
DNF changelog Plugin
======================

-----------
Description
-----------

`changelog` is a plugin for viewing package changelogs.

--------
Synopsis
--------

``dnf changelog [<options>] <package-spec>...``

---------
Arguments
---------

``<package-spec>``
    Package specification for packages to display changelogs.

-------
Options
-------

All general DNF options are accepted, see `Options` in :manpage:`dnf(8)` for details.

``--since=<date>``
   Show only changelog entries since ``<date>``. To avoid ambiguosity using YYYY-MM-DD date format is recommended.

``--count=<number>``
   Show maximum of ``<number>`` changelog entries per package.

``--upgrades``
   Show only new changelog entries for packages, that provide an upgrade for some of already installed packages.


--------
Examples
--------

Show changelogs for all packages since November 1, 2018::

   dnf changelog --since=2018-11-1

Show 3 latest changelogs of package dnf::

   dnf changelog --count=3 dnf

Show what is new in upgradable packages::

   dnf changelog --upgrades

