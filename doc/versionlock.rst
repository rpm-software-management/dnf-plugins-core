..
  Copyright (C) 2015  Red Hat, Inc.

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
DNF versionlock Plugin
================

-----------
Description
-----------

`versionlock` is a plugin that takes a set of names / versions for packages and
excludes all other versions of those packages. This allows you to protect
packages from being updated by newer versions.

The plugin provides a command `versionlock` which allows you to view and edit the
list of locked packages easily.

The plugin will walk each line of the versionlock file, parse out the name and
version of the package. It will then exclude any package by that name that
doesn't match one of the versions listed within the file. This is basically
the same as doing an exclude for the package name itself (as you cannot exclude
installed packages), but dnf will still see the versions you have
installed/versionlocked as available so that `dnf reinstall` will still
work, etc. It can also work in the opposite way, like a fast exclude,
by prefixing a '!' character to the version.

--------
Synopsis
--------

``dnf versionlock [add|exclude|list|delete|clear] [<package-spec>]``

---------
Arguments
---------

``<package-spec>``
    Package spec to lock or exclude.

-------
Subcommands
-------

``dnf versionlock add <package-spec>``
    Add a versionlock for all available packages matching the spec.

``dnf versionlock exclude <package-spec>``
    Add an exclude (within  versionlock) for the available packages matching the spec.

``dnf versionlock list``
``dnf versionlock``
    List the current versionlock entries.

``dnf versionlock delete <package-spec>``
    Remove any matching versionlock entries.

``dnf versionlock clear``
    Remove all versionlock entries.

-------------
Configuration
-------------

``/etc/dnf/plugins/versionlock.conf``

The minimal content of conf file should contain ``main`` sections with ``enabled`` and
``locklist`` parameter.


``locklist``
      This option is a string with points to the file which will have the versionlock
      information in it. Note that the file has to exist (or the versionlock plugin
      will make dnf exit).However it can be empty.

      The file takes entries in the format of ``package-spec`` (optionally prefixed with '!' for
      excludes).
      See :ref:`\specifying_packages-label`.
