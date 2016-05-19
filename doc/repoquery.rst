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

``--arch <arch>[,<arch>...]``
    Limit the resulting set only to packages of selected architectures.

``--duplicated``
    Limit the resulting set to installed duplicated packages (i.e. more package versions
    for the same name and architecture). Installonly packages are excluded from this set.

``--unneeded``
    Limit the resulting set to leaves packages that were installed as dependencies so they are no longer needed. This switch lists packages that are going to be removed after executing ``dnf autoremove`` command.

``--available``
    Limit the resulting set to available packages only (set by default).

``--extras``
    Limit the resulting set to packages that are not present in any of available repositories.

``-f <file>``, ``--file <file>``
    Limit the resulting set only to package that owns ``<file>``.

``--installed``
    Limit the resulting set to installed packges.

``--installonly``
    Limit the resulting set to installed installonly packages.

``--latest-limit <number>``
    Limit the resulting set to <number> of latest packages for every package name and architecture.
    If <number> is negative skip <number> of latest packages.

``--recent``
    Limit the resulting set to packages that were recently edited.

``--repo <repoid>``
    Limit the resulting set only to packages from repo identified by ``<repoid>``.
    Can be used multiple times with accumulative effect.

``--unsatisfied``
    Report unsatisfied dependencies among installed packages (i.e. missing requires and
    and existing conflicts).

``--upgrades``
    Limit the resulting set to packages that provide an upgrade for some already installed package.

``--whatenhances <capability>``
    Limit the resulting set only to packages that enhance ``<capability>``.

``--whatprovides <capability>``
    Limit the resulting set only to packages that provide ``<capability>``.

``--whatrecommends <capability>``
    Limit the resulting set only to packages that recommend ``<capability>``.

``--whatrequires <capability>``
    Limit the resulting set only to packages that require ``<capability>``.

``--whatsuggests <capability>``
    Limit the resulting set only to packages that suggest ``<capability>``.

``--whatsupplements <capability>``
    Limit the resulting set only to packages that supplement ``<capability>``.

``--alldeps``
    This option is stackable with ``--whatrequires`` only. Additionally it adds to the result set all packages requiring the package features.

``--srpm``
    Operate on corresponding source RPM.

Query Options
-------------

Set what information is displayed about each package.

The following are mutually exclusive, i.e. at most one can be specified. If no query option is given, matching packages are displayed in the standard NEVRA notation.

.. _info_repoquery-label:

``-i, --info``
    Show detailed information about the package.

``-l, --list``
    Show list of files in the package.

``-s, --source``
    Show package source RPM name.

``--conflicts``
    Display capabilities that the package conflicts with. Same as ``--qf "%{conflicts}``.

``--enhances``
    Display capabilities enhanced by the package. Same as ``--qf "%{enhances}""``.

``--obsoletes``
    Display capabilities that the package obsoletes. Same as ``--qf "%{obsoletes}"``.

``--provides``
    Display capabilities provided by the package. Same as ``--qf "%{provides}"``.

``--recommends``
    Display capabilities recommended by the package. Same as ``--qf "%{recommends}"``.

``--requires``
    Display capabilities that the package depends on. Same as ``--qf "%{requires}"``.

``--suggests``
    Display capabilities suggested by the package. Same as ``--qf "%{suggests}"``.

``--supplements``
    Display capabilities supplemented by the package. Same as ``--qf "%{supplements}"``.

``--tree``
    Display a recursive tree of packages with capabilities specified by one of the following supplementary options: ``--whatrequires``, ``--requires``, ``--conflicts``, ``--enhances``, ``--suggests``, ``--provides``, ``--suplements``, ``--recommends``.

``--qf <format>``, ``--queryformat <format>``
    Custom display format. ``<format>`` is a string to output for each matched package. Every occurrence of ``%{<tag>}`` within is replaced by corresponding attribute of the package. List of recognized tags can be displayed by running ``dnf repoquery --querytags``.


``--resolve``
    resolve capabilities to originating package(s).


--------
Examples
--------

Display NEVRAS of all available packages matching ``light*``::

    dnf repoquery 'light*'

Display requires of all ligttpd packages::

    dnf repoquery --requires lighttpd

Display packages providing the requires of python packages::

    dnf repoquery --requires python --resolve

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

Display duplicated packages::

    dnf repoquery --duplicated

Remove older versions of duplicated packages (an equivalent of yum's `package-cleanup --cleandups`)::

    dnf remove $(dnf repoquery --duplicated --latest-limit -1 -q)
