# needs_restarting.py
# DNF plugin to check for running binaries in a need of restarting.
#
# Copyright (C) 2014 Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#
# the mechanism of scanning smaps for opened files and matching them back to
# packages is heavily inspired by the original needs-restarting.py:
# http://yum.baseurl.org/gitweb?p=yum-utils.git;a=blob;f=needs-restarting.py

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from dnfpluginscore import logger, _

import dnf
import dnf.cli
import dbus
import functools
import os
import re
import stat
import time


# For which package updates we should recommend a reboot
# Mostly taken from https://access.redhat.com/solutions/27943
NEED_REBOOT = ['kernel', 'kernel-core', 'kernel-rt', 'glibc',
               'linux-firmware', 'systemd', 'dbus', 'dbus-broker',
               'dbus-daemon', 'microcode_ctl']

def get_options_from_dir(filepath, base):
    """
    Provide filepath as string if single dir or list of strings
    Return set of package names contained in files under filepath
    """

    if not os.path.exists(filepath):
        return set()
    options = set()
    for file in os.listdir(filepath):
        if os.path.isdir(file) or not file.endswith('.conf'):
            continue

        with open(os.path.join(filepath, file)) as fp:
            for line in fp:
                options.add((line.rstrip(), file))

    packages = set()
    for pkg in base.sack.query().installed().filter(name={x[0] for x in options}):
        packages.add(pkg.name)
    for name, file in {x for x in options if x[0] not in packages}:
        logger.warning(
            _('No installed package found for package name "{pkg}" '
                'specified in needs-restarting file "{file}".'.format(pkg=name, file=file)))
    return packages


def list_opened_files(uid):
    for (pid, smaps) in list_smaps():
        try:
            if uid is not None and uid != owner_uid(smaps):
                continue
            with open(smaps, 'r', errors='replace') as smaps_file:
                lines = smaps_file.readlines()
        except EnvironmentError:
            logger.warning("Failed to read PID %d's smaps.", pid)
            continue

        for line in lines:
            ofile = smap2opened_file(pid, line)
            if ofile is not None:
                yield ofile


def list_smaps():
    for dir_ in os.listdir('/proc'):
        try:
            pid = int(dir_)
        except ValueError:
            continue
        smaps = '/proc/%d/smaps' % pid
        yield (pid, smaps)


def memoize(func):
    sentinel = object()
    cache = {}
    def wrapper(param):
        val = cache.get(param, sentinel)
        if val is not sentinel:
            return val
        val = func(param)
        cache[param] = val
        return val
    return wrapper


def owner_uid(fname):
    return os.stat(fname)[stat.ST_UID]


def owning_package(sack, fname):
    matches = sack.query().filter(file=fname).run()
    if matches:
        return matches[0]
    return None


def print_cmd(pid):
    cmdline = '/proc/%d/cmdline' % pid
    with open(cmdline) as cmdline_file:
        command = dnf.i18n.ucd(cmdline_file.read())
    command = ' '.join(command.split('\000'))
    print('%d : %s' % (pid, command))


def get_service_dbus(pid):
    bus = dbus.SystemBus()
    systemd_manager_object = bus.get_object(
        'org.freedesktop.systemd1',
        '/org/freedesktop/systemd1'
    )
    systemd_manager_interface = dbus.Interface(
        systemd_manager_object,
        'org.freedesktop.systemd1.Manager'
    )

    service_unit_path = None
    try:
        service_unit_path = systemd_manager_interface.GetUnitByPID(pid)
    except dbus.DBusException as e:
        # There is no unit for the pid. Usually error is 'NoUnitForPid'.
        # Considering what we do at the bottom (just return if not service)
        # Then there's really no reason to exit here on that exception.
        # Log what's happened then move on.
        msg = str(e)
        if msg.startswith('org.freedesktop.systemd1.NoUnitForPID'):
            logger.warning("Failed to get systemd unit for PID {}: {}".format(pid, msg))
            return
        else:
            raise

    service_proxy = bus.get_object('org.freedesktop.systemd1', service_unit_path)
    service_properties = dbus.Interface(
        service_proxy, dbus_interface="org.freedesktop.DBus.Properties")
    name = service_properties.Get(
        "org.freedesktop.systemd1.Unit",
        'Id'
    )
    if name.endswith(".service"):
        return name
    return

def smap2opened_file(pid, line):
    slash = line.find('/')
    if slash < 0:
        return None
    fn = line[slash:].strip()
    suffix_index = fn.rfind(' (deleted)')
    if suffix_index < 0:
        return OpenedFile(pid, fn, False)
    else:
        return OpenedFile(pid, fn[:suffix_index], True)


class OpenedFile(object):
    RE_TRANSACTION_FILE = re.compile('^(.+);[0-9A-Fa-f]{8,}$')

    def __init__(self, pid, name, deleted):
        self.deleted = deleted
        self.name = name
        self.pid = pid

    @property
    def presumed_name(self):
        """Calculate the name of the file pre-transaction.

        In case of a file that got deleted during the transaction, possibly
        just because of an upgrade to a newer version of the same file, RPM
        renames the old file to the same name with a hexadecimal suffix just
        before delting it.

        """

        if self.deleted:
            match = self.RE_TRANSACTION_FILE.match(self.name)
            if match:
                return match.group(1)
        return self.name

class ProcessStart(object):
    def __init__(self):
        self.kernel_boot_time = ProcessStart.get_kernel_boot_time()
        self.boot_time = ProcessStart.get_boot_time(self.kernel_boot_time)
        self.sc_clk_tck = ProcessStart.get_sc_clk_tck()

    @staticmethod
    def get_kernel_boot_time():
        try:
            with open('/proc/stat', 'r') as file:
                for line in file:
                    if line.startswith("btime "):
                        key, value = line.split()
                        return float(value)
        except OSError as e:
            logger.debug("Couldn't read /proc/stat: %s", e)
        return 0

    @staticmethod
    def get_boot_time(kernel_boot_time):
        """
        We have three sources from which to derive the boot time. These values vary
        depending on containerization, existence of a Real Time Clock, etc.
        - UnitsLoadStartTimestamp property on /org/freedesktop/systemd1
             The start time of the service manager, according to systemd itself.
             Seems to be more reliable than UserspaceTimestamp when the RTC is
             in local time. Works unless the system was not booted with systemd,
             such as in (most) containers.
        - st_mtime of /proc/1
             Reflects the time the first process was run after booting. This
             works for all known cases except machines without a RTC---they
             awake at the start of the epoch.
        - btime field of /proc/stat
             Reflects the time when the kernel started. Works for machines
             without RTC iff the current time is reasonably correct. Does not
             work on containers which share their kernel with the host---there,
             the host kernel uptime is returned.
        """

        units_load_start_timestamp = None
        try:
            # systemd timestamps are the preferred method to determine boot
            # time. max(proc_1_boot_time, kernel_boot_time) does not allow us
            # to disambiguate between an unreliable RTC (e.g. the RTC is in
            # UTC+1 instead of UTC) and a container with a proc_1_boot_time >
            # kernel_boot_time. So we use UnitsLoadStartTimestamp if it's
            # available, else fall back to the other methods.
            bus = dbus.SystemBus()
            systemd1 = bus.get_object(
                'org.freedesktop.systemd1',
                '/org/freedesktop/systemd1'
            )
            props = dbus.Interface(
                systemd1,
                dbus.PROPERTIES_IFACE
            )
            units_load_start_timestamp = props.Get(
                'org.freedesktop.systemd1.Manager',
                'UnitsLoadStartTimestamp'
            )
            if units_load_start_timestamp != 0:
                systemd_boot_time = units_load_start_timestamp / (1000 * 1000)
                logger.debug("Got boot time from systemd: %s", systemd_boot_time)
                return systemd_boot_time
        except dbus.exceptions.DBusException as e:
            logger.debug("D-Bus error getting boot time from systemd: %s", e)

        logger.debug("Couldn't get boot time from systemd, checking st_mtime of /proc/1 and btime field of /proc/stat.")

        try:
            proc_1_boot_time = float(os.stat('/proc/1').st_mtime)
        except OSError as e:
            logger.debug("Couldn't stat /proc/1: %s", e)
            proc_1_boot_time = 1
        kernel_boot_time = kernel_boot_time

        boot_time = max(proc_1_boot_time, kernel_boot_time)

        logger.debug("st_mtime of /proc/1: %s", proc_1_boot_time)
        logger.debug("btime field of /proc/stat: %s", kernel_boot_time)
        logger.debug("Using %s as the system boot time.", boot_time)

        return boot_time

    @staticmethod
    def get_sc_clk_tck():
        return os.sysconf(os.sysconf_names['SC_CLK_TCK'])

    def __call__(self, pid):
        stat_fn = '/proc/%d/stat' % pid
        with open(stat_fn) as stat_file:
            stats = stat_file.read().split()
        ticks_after_kernel_boot = int(stats[21])
        secs_after_kernel_boot = ticks_after_kernel_boot / self.sc_clk_tck

        # The process's start time is always measured relative to the kernel
        # start time, not either of the other methods we use to get "boot time".
        return self.kernel_boot_time + secs_after_kernel_boot


@dnf.plugin.register_command
class NeedsRestartingCommand(dnf.cli.Command):
    aliases = ('needs-restarting',)
    summary = _('determine updated binaries that need restarting')

    @staticmethod
    def set_argparser(parser):
        parser.add_argument('-u', '--useronly', action='store_true',
                            help=_("only consider this user's processes"))
        parser.add_argument('-r', '--reboothint', action='store_true',
                            help=_("only report whether a reboot is required "
                                   "(exit code 1) or not (exit code 0)"))
        parser.add_argument('-s', '--services', action='store_true',
                            help=_("only report affected systemd services"))
        parser.add_argument('--exclude-services', action='store_true',
                            help=_("don't list stale processes that correspond to a systemd service"))

    def configure(self):
        demands = self.cli.demands
        demands.sack_activation = True
        self.base.conf.optional_metadata_types += ["filelists"]

    def run(self):
        process_start = ProcessStart()
        owning_pkg_fn = functools.partial(owning_package, self.base.sack)
        owning_pkg_fn = memoize(owning_pkg_fn)

        opt = get_options_from_dir(os.path.join(
            self.base.conf.installroot,
            "etc/dnf/plugins/needs-restarting.d/"),
            self.base)
        NEED_REBOOT.extend(opt)
        if self.opts.reboothint:
            need_reboot = set()
            installed = self.base.sack.query().installed()
            for pkg in installed.filter(provides=NEED_REBOOT):
                if pkg.installtime > process_start.boot_time:
                    need_reboot.add(pkg.name)
            if need_reboot:
                print(_('Core libraries or services have been updated '
                        'since boot-up:'))
                for name in sorted(need_reboot):
                    print('  * %s' % name)
                print()
                print(_('Reboot is required to fully utilize these updates.'))
                print(_('More information:'),
                      'https://access.redhat.com/solutions/27943')
                raise dnf.exceptions.Error()  # Sets exit code 1
            else:
                print(_('No core libraries or services have been updated '
                        'since boot-up.'))
                print(_('Reboot should not be necessary.'))
                return None

        stale_pids = set()
        stale_service_names = set()
        uid = os.geteuid() if self.opts.useronly else None
        for ofile in list_opened_files(uid):
            pkg = owning_pkg_fn(ofile.presumed_name)
            pid = ofile.pid
            if pkg is None:
                continue
            if pkg.installtime <= process_start(pid):
                continue
            if self.opts.services or self.opts.exclude_services:
                service_name = get_service_dbus(pid)
                if service_name is None:
                    stale_pids.add(pid)
                else:
                    stale_service_names.add(service_name)
                    if not self.opts.exclude_services:
                        stale_pids.add(pid)
            else:
                # If neither --services nor --exclude-services is set, don't
                # query D-Bus at all.
                stale_pids.add(pid)

        if self.opts.services:
            for stale_service_name in sorted(stale_service_names):
                print(stale_service_name)
            return 0

        for pid in sorted(stale_pids):
            print_cmd(pid)
