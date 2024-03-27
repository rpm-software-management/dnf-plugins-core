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

``dnf needs-restarting [-u] [-r] [-s]``

-----------
Description
-----------

`needs-restarting` looks through running processes and tries to detect those that use files from packages that have been updated after the given process started. Such processes are reported by this tool.

Note that in most cases a process should survive update of its binary and libraries it is using without requiring to be restarted for proper operation. There are however specific cases when this does not apply. Separately, processes often need to be restarted to reflect security updates.

.. note::
   Needs-restarting will try to guess the boot time using three different methods:

   ``UnitsLoadStartTimestamp``
        D-Bus property on ``/org/freedesktop/systemd1``.
        Works unless the system was not booted with systemd,
        such as in (most) containers.
   ``st_mtime of /proc/1``
        Reflects the time the first process was run after booting.
        This works for all known cases except machines without
        a RTC—they awake at the start of the epoch.
   ``/proc/uptime``
        Seconds field of ``/proc/uptime`` subtracted from the current time.
        Works for machines without RTC if the current time is reasonably correct.
        Does not work on containers which share their kernel with the
        host—there, the host kernel uptime is returned.


.. warning::
    Some systems are configured to read the RTC time in the local time
    zone. This mode cannot be fully supported. It will create various problems
    with time zone changes and daylight saving time adjustments. The RTC time
    is never updated, it relies on external facilities to maintain it. **If at
    all possible, use RTC in UTC by calling** ``timedatectl set-local-rtc 0``.
    See ``man timedatectl`` for more information.

-------
Options
-------

All general DNF options are accepted, see `Options` in :manpage:`dnf(8)` for details.

``-u, --useronly``
    Only consider processes belonging to the running user.

``-r, --reboothint``
    Only report whether a reboot is required (exit code 1) or not (exit code 0).

``-s, --services``
    Only list the affected systemd services.

-------------
Configuration
-------------

``/etc/dnf/plugins/needs-restarting.d/``

``/etc/dnf/plugins/needs-restarting.d/pkgname.conf``

Packages can be added to ``needs-restarting`` via conf files in config
directory. Config files need to have ``.conf`` extension or will be ignored.

More than one package is allowed in each file (one package per line) although
it is advised to use one file for each package.

Example::

        echo "dwm" > /etc/dnf/plugins/needs-restarting.d/dwm.conf
