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

=====================
 DNF download Plugin
=====================

Download binary or source packages.

--------
Synopsis
--------

``dnf download [options] <pkg-spec>...``

---------
Arguments
---------

``<pkg-spec>``
    Package specification for the package to download.

-------
Options
-------

``--help-cmd``
    Show this help.

``--source``
    Download the source rpm. Enables source repositories of all enabled binary repositories.

``--destdir``
    Download directory, default is the current directory (the directory must exist).

``--resolve``
    Resolve and download dependencies, not installed on the local system.

--------
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
