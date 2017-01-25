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

================
DNF local Plugin
================

-----------
Description
-----------

Automatically copy all downloaded packages to a repository on the local filesystem and generating repo metadata.

.. note:: Generating repo metadata will work only if you have installed ``createrepo_c`` package.


-------------
Configuration
-------------

``/etc/dnf/plugins/local.conf``

The minimal content of conf file should contain ``main`` and ``createrepo`` sections with ``enabled`` parameter, otherwise plugin will not work.::

  [main]
  enabled = true

  [createrepo]
  enabled = true

For ``main`` section you can specify ``repodir`` paramater which sets path to local repository.

Other options and comments you can find in configuration file.
