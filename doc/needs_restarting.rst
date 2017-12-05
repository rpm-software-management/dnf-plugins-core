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

===========================
DNF needs-restarting Plugin
===========================

Check for running processes that should be restarted.

--------
Synopsis
--------

``dnf needs-restarting [-u]``

-----------
Description
-----------

`needs-restarting` looks through running processes and tries to detect those that use files from packages that have been updated after the given process started. Such processes are reported by this tool.

Note that in most cases a process should survive update of its binary and libraries it is using without requiring to be restarted for proper operation. There are however specific cases when this does not apply. Separately, processes often need to be restarted to reflect security updates.

-------
Options
-------

``-u, --useronly``

    Only consider processes belonging to the running user.
