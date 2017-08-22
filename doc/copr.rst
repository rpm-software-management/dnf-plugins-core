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

----------------------
Arguments (playground)
----------------------

``enable``
    Enable the Playground repository.

``disable``
    Disable the Playground repository.

``upgrade``
    Upgrade the Playground repository settings (same as ``disable`` and then ``enable``).

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
