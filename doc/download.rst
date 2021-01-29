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
    Local RPMs can be specified as well. This is useful with the ``--source``
    option or if you want to download the same RPM again.

-------
Options
-------

All general DNF options are accepted, see `Options` in :manpage:`dnf(8)` for details.

``--help-cmd``
    Show this help.

``--arch <arch>[,<arch>...]``
    Limit the query to packages of given architectures (default is all compatible architectures with
    your system). To download packages with arch incompatible with your system use
    ``--forcearch=<arch>`` option to change basearch.

``--source``
    Download the source rpm. Enables source repositories of all enabled binary repositories.

``--debuginfo``
    Download the debuginfo rpm. Enables debuginfo repositories of all enabled binary repositories.

``--downloaddir``
    Download directory, default is the current directory (the directory must exist).

``--url``
    Instead of downloading, print list of urls where the rpms can be downloaded.

``--urlprotocol``
    Limit the protocol of the urls output by the --url option. Options are http, https, rsync, ftp.

``--resolve``
    Resolves dependencies of specified packages and downloads missing dependencies in the system.

``--alldeps``
    When used with ``--resolve``, download all dependencies (do not skip already installed ones).

--------
Examples
--------
``dnf download dnf``
    Download the latest dnf package to the current directory.

``dnf download --url dnf``
    Just print the remote location url where the dnf rpm can be downloaded from.

``dnf download --url --urlprotocols=https --urlprotocols=rsync dnf``
    Same as above, but limit urls to https or rsync urls.

``dnf download dnf --destdir /tmp/dnl``
    Download the latest dnf package to the /tmp/dnl directory (the directory must exist).

``dnf download dnf --source``
    Download the latest dnf source package to the current directory.

``dnf download rpm --debuginfo``
    Download the latest rpm-debuginfo package to the current directory.

``dnf download btanks --resolve``
    Download the latest btanks package and the uninstalled dependencies to the current directory.
