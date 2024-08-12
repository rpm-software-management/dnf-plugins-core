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
DNF copr Plugin
===============

Work with Copr & Playground repositories on the local system.

* The ``copr`` command is used to add or remove Copr repositories to the local system
* The ``playground`` is used to enable or disable the Playground repository

--------
Synopsis
--------

``dnf copr [enable|disable|remove|list|search] <parameters>``

``dnf playground [enable|disable|upgrade]``

----------------
Arguments (copr)
----------------

``enable name/project [chroot]``
    Enable the ``name/project`` Copr repository with the optional ``chroot``.

``disable name/project``
    Disable the ``name/project`` Copr repository.

``remove name/project``
    Remove the ``name/project`` Copr repository.

``list --installed``
    List installed Copr repositories (default).

``list --enabled``
    List enabled Copr repositories.

``list --disabled``
    List disabled Copr repositories.

``list --available-by-user=name``
    List available Copr repositories for a given ``name``.

``search project``
    Search for a given ``project``.

``enable hub/name/project``
    Enable the ``name/project`` Copr repository from the specified Copr ``hub``,
    Hub is be specified either by its hostname (eg. `copr.fedorainfracloud.org`)
    or by an ID that's defined in a configuration file.

--------------
Options (copr)
--------------

All general DNF options are accepted, see `Options` in :manpage:`dnf(8)` for details.

``--hub Copr``
    Specify a Copr hub to use. Default is the Fedora Copr: ``https://copr.fedorainfracloud.org``.

--------------------
Configuration (copr)
--------------------

``/etc/dnf/plugins/copr.conf``
``/etc/dnf/plugins/copr.d/``
``/usr/share/dnf/plugins/copr.vendor.conf``

Configuration file should contain a section for each hub, each section having ``hostname``
 (mandatory), ``protocol`` (default ``https``) and ``port`` (default ``443``) parameters.::

  [fedora]
  hostname = copr.fedorainfracloud.org
  protocol = https
  port = 443


There is also a vendor configuration that allows a vendor to specify the distro ID that copr should use by default.
This is useful for vendors that want to use Copr for their own distro. The vendor configuration is in
``/usr/share/dnf/plugins/copr.vendor.conf`` (optional) or ``/etc/dnf/plugins/copr.conf``::

  [main]
  distribution = fedora
  releasever = 37
----------------------
Arguments (playground)
----------------------

``enable``
    Enable the Playground repository.

``disable``
    Disable the Playground repository.

``upgrade``
    Upgrade the Playground repository settings (same as ``disable`` and then ``enable``).

--------------------
Options (playground)
--------------------

All general DNF options are accepted, see `Options` in :manpage:`dnf(8)` for details.

--------
Examples
--------

``copr enable rhscl/perl516 epel-6-x86_64``
    Enable the ``rhscl/perl516`` Copr repository, using the ``epel-6-x86_64`` chroot.

``copr disable rhscl/perl516``
    Disable the ``rhscl/perl516`` Copr repository

``copr list --available-by-user=rita``
    List available Copr projects for user ``rita``.

``copr search tests``
    Search for Copr projects named ``tests``.

------------
Known issues
------------

Copr plugin does not respect `-4` and `-6` options of `dnf` command when enabling a Copr
respository. Users are advised to configure a global address preference in /etc/gai.conf.
