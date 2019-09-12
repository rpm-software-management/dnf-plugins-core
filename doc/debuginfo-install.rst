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

============================
DNF debuginfo-install Plugin
============================

Install the associated debuginfo packages for a given package specification.

--------
Synopsis
--------

``dnf debuginfo-install <pkg-spec>...``

---------
Arguments
---------

``<pkg-spec>``
    The package to install the associated debuginfo package for.

-------
Options
-------

All general DNF options are accepted, see `Options` in :manpage:`dnf(8)` for details.

-------------
Configuration
-------------

``/etc/dnf/plugins/debuginfo-install.conf``

The minimal content of conf file should contain ``main`` sections with ``enabled`` and
``autoupdate`` parameter.

``autoupdate``
    A boolean option which controls updates of debuginfo packages. If options is enabled
    and there are debuginfo packages installed it automatically enables all configured
    debuginfo repositories.
    (Disabled by default.)

--------
Examples
--------

``dnf debuginfo-install foobar``
    Install the debuginfo packages for the foobar package.

``dnf upgrade --enablerepo=*-debuginfo <package-name>-debuginfo``
    Upgrade debuginfo package of a <package-name>.

``dnf upgrade --enablerepo=*-debuginfo "*-debuginfo"``
    Upgrade all debuginfo packages.
