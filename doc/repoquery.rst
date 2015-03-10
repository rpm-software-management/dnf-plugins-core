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

====================
DNF repoquery Plugin
====================

Query package information from Yum repositories.

--------
Synopsis
--------

``dnf repoquery [<select-options>] [<query-options>] [<pkg-spec>]``
``dnf repoquery --querytags``

-----------
Description
-----------

`repoquery` searches the available Yum repositories for selected packages and displays the requested information about them. It is an equivalent of ``rpm -q`` for remote repositories.


Select Options
--------------

Together with ``<pkg-spec>``, control what packages are displayed in the output. If ``<pkg-spec>`` is given, the set of resulting packages matching the specification. All packages are considered if no ``<pkg-spec>`` is specified.

``<pkg-spec>``
    Package specification like: name[-[epoch:]version[-release]][.arch]. See
    http://dnf.readthedocs.org/en/latest/command_ref.html#specifying-packages

``--arch <arch>``
    Limit the resulting set only to packages of arch ``<arch>``.

``-f <file>``, ``--file <file>``
    Limit the resulting set only to package that owns ``<file>``.

``--repoid <id>``
    Limit the resulting set only to packages from repo identified by ``<id>``.

``--whatprovides <capability>``
    Limit the resulting set only to packages that provide ``<capability>``.

``--whatrequires <capability>``
    Limit the resulting set only to packages that require ``<capability>``.


Query Options
-------------

Set what information is displayed about each package.

The following are mutually exclusive, i.e. at most one can be specified. If no query option is given, matching packages are displayed in the standard NEVRA notation.

``--conflicts``
    Display capabilities that the package conflicts with. Same as ``--qf "%{conflicts}``.

.. _info_repoquery-label:

``-i, --info``
    Show detailed information about the package.

``-l, --list``
    Show list of files in the package.

``-s, --source``
    Show package source RPM name.

``--obsoletes``
    Display capabilities that the package obsoletes. Same as ``--qf "%{obsoletes}``.

``--provides``
    Display capabilities provided by the package. Same as ``--qf "%{provides}``.

``--qf <format>``, ``--queryformat <format>``
    Custom display format. ``<format>`` is a string to output for each matched package. Every occurrence of ``%{<tag>}`` within is replaced by corresponding attribute of the package. List of recognized tags can be displayed by running ``dnf repoquery --querytags``.

``--requires``
    Display capabilities that the package depends on. Same as ``--qf "%{requires}``.


--------
Examples
--------

Display NEVRAS of all available packages matching ``light*``::

    dnf repoquery 'light*'

Display requires of all ligttpd packages::

    dnf repoquery --requires lighttpd

Display source rpm of ligttpd package::

    dnf repoquery --source lighttpd

Display package name that owns the given file::

    dnf repoquery --file /etc/lighttpd/lighttpd.conf

Display name, architecture and the containing repository of all lighttpd packages::

    dnf repoquery --queryformat '%{name}.%{arch} : %{reponame}' lighttpd

Display all available packages providing "webserver"::

    dnf repoquery --whatprovides webserver

Display all available packages providing "webserver" but only for "i686" architecture::

    dnf repoquery --whatprovides webserver --arch i686
