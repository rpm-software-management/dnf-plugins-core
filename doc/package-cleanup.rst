..
  Copyright (C) 2014  Red Hat, Inc.

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

===============
Package Cleanup
===============

A DNF-based shim imitating the original YUM-based package-cleanup utility.

--------
Synopsis
--------

``package-cleanup [options]``

-------
Options
-------

All general DNF options are accepted, see `Options` in :manpage:`dnf(8)` for details.

``--leaves``
    List leaf nodes in the local RPM database.
    Leaf nodes are RPMs that are not relied upon by any other RPM.
    Maps to ``dnf repoquery --unneeded``.

``--orphans``
    List installed packages which are not available from currently configured
    repositories.
    Maps to ``dnf repoquery --extras``.

``--problems``
    List dependency problems in the local RPM database.
    Maps to ``dnf repoquery --unsatisfied``.

``--dupes``
    Scan for duplicates in the local RPM database.
    Maps to ``dnf repoquery --duplicates``.

``--cleandupes``
    Scan for duplicates in the local RPM database and clean out the older
    versions.
    Maps to ``dnf remove --duplicates``.

--------
Examples
--------

``package-cleanup --problems``
    List all dependency problems.

``package-cleanup --orphans``
    List all packages that are not in any DNF repository.

``package-cleanup --cleandupes``
    Remove all packages that have a duplicate installed.
