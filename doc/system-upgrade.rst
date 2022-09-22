..
  Copyright (C) 2014-2016 Red Hat, Inc.

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

=========================
DNF system-upgrade Plugin
=========================

-----------
Description
-----------

DNF system-upgrades plugin provides three commands: ``system-upgrade``, ``offline-upgrade``, and
``offline-distrosync``. Only ``system-upgrade`` command requires increase of distribution major
version (``--releasever``) compared to installed version.

``dnf system-upgrade`` can be used to upgrade a Fedora system to a new major
release. It replaces fedup (the old Fedora Upgrade tool). Before you proceed ensure that your system
is fully upgraded (``dnf --refresh upgrade``).

The ``system-upgrade`` command also performes additional actions necessary for the upgrade of the
system, for example an upgrade of groups and environments.

--------
Synopsis
--------

``dnf system-upgrade download --releasever VERSION [OPTIONS]``

``dnf system-upgrade reboot``

``dnf system-upgrade clean``

``dnf system-upgrade log``

``dnf system-upgrade log --number=<number>``

``dnf offline-upgrade download [OPTIONS]``

``dnf offline-upgrade reboot``

``dnf offline-upgrade clean``

``dnf offline-upgrade log``

``dnf offline-upgrade log --number=<number>``

``dnf offline-distrosync download [OPTIONS]``

``dnf offline-distrosync reboot``

``dnf offline-distrosync clean``

``dnf offline-distrosync log``

``dnf offline-distrosync log --number=<number>``

-----------
Subcommands
-----------

``download``
    Downloads everything needed to upgrade to a new major release.

``reboot``
    Prepares the system to perform the upgrade, and reboots to start the upgrade.
    This can only be used after the ``download`` command completes successfully.

``clean``
    Remove previously-downloaded data. This happens automatically at the end of
    a successful upgrade.

``log``
    Used to see a list of boots during which an upgrade was attempted, or show
    the logs from an upgrade attempt. The logs for one of the boots can be shown
    by specifying one of the numbers in the first column. Negative numbers can
    be used to number the boots from last to first. For example, ``log --number=-1`` can
    be used to see the logs for the last upgrade attempt.

-------
Options
-------

``--releasever=VERSION``
    REQUIRED. The version to upgrade to. Sets ``$releasever`` in all enabled
    repos. Usually a number, or ``rawhide``.

``--downloaddir=<path>``
    Redirect download of packages to provided ``<path>``. By default, packages
    are downloaded into (per repository created) subdirectories of
    /var/lib/dnf/system-upgrade.

``--distro-sync``
    Behave like ``dnf distro-sync``: always install packages from the new
    release, even if they are older than the currently-installed version. This
    is the default behavior.

``--no-downgrade``
    Behave like ``dnf update``: do not install packages from the new release
    if they are older than what is currently installed. This is the opposite of
    ``--distro-sync``. If both are specified, the last option will be used. The option cannot be
    used with the ``offline-distrosync`` command.

``--number``
    Applied with ``log`` subcommand will show the log specified by the number.

-----
Notes
-----

``dnf system-upgrade reboot`` does not create a "System Upgrade" boot item. The
upgrade will start regardless of which boot item is chosen.

The ``DNF_SYSTEM_UPGRADE_NO_REBOOT`` environment variable can be set to a
non-empty value to disable the actual reboot performed by ``system-upgrade``
(e.g. for testing purposes).

Since this is a DNF plugin, options accepted by ``dnf`` are also valid here,
such as ``--allowerasing``.
See :manpage:`dnf(8)` for more information.

The ``fedup`` command is not provided, not even as an alias for
``dnf system-upgrade``.

----
Bugs
----

Upgrading from install media (e.g. a DVD or .iso file) currently requires the
user to manually set up a DNF repo and fstab entry for the media.

--------
Examples
--------

Typical upgrade usage
---------------------

``dnf --refresh upgrade``

``dnf system-upgrade download --releasever 26``

``dnf system-upgrade reboot``

Show logs from last upgrade attempt
-----------------------------------

``dnf system-upgrade log --number=-1``

--------------
Reporting Bugs
--------------

Bugs should be filed here:

  https://bugzilla.redhat.com/

For more info on filing bugs, see the Fedora Project wiki:

  https://fedoraproject.org/wiki/How_to_file_a_bug_report

  https://fedoraproject.org/wiki/Bugs_and_feature_requests

Please include ``/var/log/dnf.log`` and the output of
``dnf system-upgrade log --number=-1`` (if applicable) in your bug reports.

Problems with dependency solving during download are best reported to the
maintainers of the package(s) with the dependency problems.

Similarly, problems encountered on your system after the upgrade completes
should be reported to the maintainers of the affected components. In other
words: if (for example) KDE stops working, it's best if you report that to
the KDE maintainers.

--------
See Also
--------

:manpage:`dnf(8)`,
:manpage:`dnf.conf(5)`,
:manpage:`journalctl(1)`.

Project homepage
----------------

https://github.com/rpm-software-management/dnf-plugins-core

-------
Authors
-------

Will Woods <wwoods@redhat.com>

Štěpán Smetana <ssmetana@redhat.com>
