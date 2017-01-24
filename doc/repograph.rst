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

====================
DNF repograph Plugin
====================

Output a full package dependency graph in dot format.

--------
Synopsis
--------

``dnf repograph [<options>]``
``dnf repo-graph [<options>]``

-----------
Description
-----------

`repograph` is a program that generates a full package dependency list from a repository and outputs it in dot format.


Options
-------

Set what repos should be processed.

``--repo <repoid>``
    Specify repo ids to query, can be specified multiple times (default is all enabled).


--------
Examples
--------

Output dependency list from all enabled repositories::

    dnf repograph

Output dependency list from rawhide repository::

    dnf repograph --repoid rawhide

Output dependency list from rawhide and koji repository::

    dnf repo-graph --repoid rawhide --repoid koji
