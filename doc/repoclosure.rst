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

======================
DNF repoclosure Plugin
======================

Display a list of unresolved dependencies for repositories.

--------
Synopsis
--------

``dnf repoclosure [<options>]``

-----------
Description
-----------

`repoclosure` is a program that reads package metadata from one or more repositories, checks all dependencies, and displays a list of packages with unresolved dependencies.


Options
-------

``--arch <arch>``
    Query only packages for specified architecture, can be specified multiple times (default is all architectures).

``--best``
    Check only the newest packages per arch.

``--check <repoid>``
    Specify repo ids to check, can be specified multiple times (default is all enabled).

``--newest``
    Check only the newest packages in the repos.

``--pkg <pkg``
    Check closure for this package only.

``--repo <repoid>``
    Specify repo ids to query, can be specified multiple times (default is all enabled).


--------
Examples
--------

Display list of unresolved dependencies for all enabled repositories::

    dnf repoclosure

Display list of unresolved dependencies for rawhide repository and packages with architecture noarch and x86_64::

    dnf repoclosure --repoid rawhide --arch noarch --arch x86_64

Display list of unresolved dependencies for zmap package from rawhide repository::

    dnf repoclosure --repoid rawhide --pkg zmap

Display list of unresolved dependencies for myrepo, an add-on for the rawhide repository::

    dnf repoclosure --repoid rawhide --check myrepo

