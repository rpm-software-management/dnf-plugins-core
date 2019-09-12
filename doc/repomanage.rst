..
  Copyright (C) 2015 Igor Gnatenko

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
DNF repomanage Plugin
=====================

Manage a directory of rpm packages.

--------
Synopsis
--------

``dnf repomanage [<optional-options>] [<options>] <path>``

-----------
Description
-----------

`repomanage` prints newest or oldest packages in specified directory for easy piping to xargs or similar programs.


Options
-------

All general DNF options are accepted, see `Options` in :manpage:`dnf(8)` for details.

The following options set what packages are displayed. These options are mutually exclusive, i.e. only one can be specified. If no option is specified, the newest packages are shown.

``--old``
    Show older packages.

``--new``
    Show newest packages.

The following options control how packages are displayed in the output:

``-s``, ``--space``
    Print resulting set separated by space instead of newline.

``-k <keep-number>``, ``--keep <keep-number>``
    Limit the resulting set to newest ``<keep-number>`` packages.


--------
Examples
--------

Display newest packages in current directory::

    dnf repomanage --new .

Display 2 newest packages in requires "home" directory::

    dnf repomanage --new --keep 2 ~/

Display older package separated by space in current directory::

    dnf repomanage --old --space .
