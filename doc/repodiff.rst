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
DNF repodiff Plugin
======================

Display a list of differences between two or more repositories

--------
Synopsis
--------

``dnf repodiff [<options>]``

-----------
Description
-----------

`repodiff` is a program which will list differences between two sets of repositories.  Note that by default only source packages are compared.


Options
-------

All general DNF options are accepted, see `Options` in :manpage:`dnf(8)` for details.

``--repo-old=<repoid>, -o <repoid>``
    Add a ``<repoid>`` as an old repository. It is possible to be used in conjunction with ``--repofrompath`` option. Can be specified multiple times. 

``--repo-new=<repoid>, -n <repoid>``
    Add a ``<repoid>`` as a new repository. Can be specified multiple times.

``--archlist=<arch>, -a <arch>``
    Add architectures to change the default from just comparing source packages. Note that you can use a wildcard "*" for all architectures. Can be specified multiple times.

``--size, -s``
    Output additional data about the size of the changes.

``--compare-arch``
    Normally packages are just compared based on their name, this flag makes the comparison also use the arch. So foo.noarch and foo.x86_64 are considered to be a different packages.

``--simple``
    Output a simple one line message for modified packages.

``--downgrade``
    Split the data for modified packages between upgraded and downgraded packages.


--------
Examples
--------

Compare source pkgs in two local repos::

    dnf repodiff --repofrompath=o,/tmp/repo-old --repofrompath=n,/tmp/repo-new --repo-old=o --repo-new=n

Compare x86_64 compat. binary pkgs in two remote repos, and two local one::

    dnf repodiff --repofrompath=o,http://example.com/repo-old --repofrompath=n,http://example.com/repo-new --repo-old=o --repo-new=n --archlist=x86_64

Compare x86_64 compat. binary pkgs, but also compare architecture::

    dnf repodiff --repofrompath=o,http://example.com/repo-old --repofrompath=n,http://example.com/repo-new --repo-old=o --repo-new=n --archlist=x86_64 --compare-arch


