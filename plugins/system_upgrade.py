# -*- coding: utf-8 -*-
#
# Copyright (c) 2015-2020 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author(s): Will Woods <wwoods@redhat.com>

"""system_upgrade.py - DNF plugin to handle major-version system upgrades."""

from subprocess import call, Popen, check_output, CalledProcessError
import json
import os
import os.path
import re
import sys
import uuid

from systemd import journal

from dnfpluginscore import _, logger

import dnf
import dnf.cli
from dnf.cli import CliError
from dnf.i18n import ucd
import dnf.transaction
from dnf.transaction_sr import serialize_transaction, TransactionReplay

import libdnf.conf


# Translators: This string is only used in unit tests.
_("the color of the sky")

DOWNLOAD_FINISHED_ID = uuid.UUID('9348174c5cc74001a71ef26bd79d302e')
REBOOT_REQUESTED_ID = uuid.UUID('fef1cc509d5047268b83a3a553f54b43')
UPGRADE_STARTED_ID = uuid.UUID('3e0a5636d16b4ca4bbe5321d06c6aa62')
UPGRADE_FINISHED_ID = uuid.UUID('8cec00a1566f4d3594f116450395f06c')

ID_TO_IDENTIFY_BOOTS = UPGRADE_STARTED_ID

PLYMOUTH = '/usr/bin/plymouth'

RELEASEVER_MSG = _(
    "Need a --releasever greater than the current system version.")
DOWNLOAD_FINISHED_MSG = _(  # Translators: do not change "reboot" here
    "Download complete! Use 'dnf {command} reboot' to start the upgrade.\n"
    "To remove cached metadata and transaction use 'dnf {command} clean'")
CANT_RESET_RELEASEVER = _(
    "Sorry, you need to use 'download --releasever' instead of '--network'")

STATE_VERSION = 3

# --- Miscellaneous helper functions ------------------------------------------


def reboot(poweroff = False):
    if os.getenv("DNF_SYSTEM_UPGRADE_NO_REBOOT", default=False):
        logger.info(_("Reboot turned off, not rebooting."))
    else:
        if poweroff:
            Popen(["systemctl", "poweroff"])
        else:
            Popen(["systemctl", "reboot"])


def get_url_from_os_release():
    key = "UPGRADE_GUIDE_URL="
    for path in ["/etc/os-release", "/usr/lib/os-release"]:
        try:
            with open(path) as release_file:
                for line in release_file:
                    line = line.strip()
                    if line.startswith(key):
                        return line[len(key):].strip('"')
        except IOError:
            continue
    return None


# DNF-FIXME: dnf.util.clear_dir() doesn't delete regular files :/
def clear_dir(path, ignore=[]):
    if not os.path.isdir(path):
        return

    for entry in os.listdir(path):
        fullpath = os.path.join(path, entry)
        if fullpath in ignore:
            continue
        try:
            if os.path.isdir(fullpath):
                dnf.util.rm_rf(fullpath)
            else:
                os.unlink(fullpath)
        except OSError:
            pass


def check_release_ver(conf, target=None):
    if dnf.rpm.detect_releasever(conf.installroot) == conf.releasever:
        raise CliError(RELEASEVER_MSG)
    if target and target != conf.releasever:
        # it's too late to set releasever here, so this can't work.
        # (see https://bugzilla.redhat.com/show_bug.cgi?id=1212341)
        raise CliError(CANT_RESET_RELEASEVER)


def disable_blanking():
    try:
        tty = open('/dev/tty0', 'wb')
        tty.write(b'\33[9;0]')
    except Exception as e:
        print(_("Screen blanking can't be disabled: %s") % e)

# --- State object - for tracking upgrade state between runs ------------------


# DNF-INTEGRATION-NOTE: basically the same thing as dnf.persistor.JSONDB
class State(object):
    def __init__(self, statefile):
        self.statefile = statefile
        self._data = {}
        self._read()

    def _read(self):
        try:
            with open(self.statefile) as fp:
                self._data = json.load(fp)
        except IOError:
            self._data = {}
        except ValueError:
            self._data = {}
            logger.warning(_("Failed loading state file: %s, continuing with "
                             "empty state."), self.statefile)

    def write(self):
        dnf.util.ensure_dir(os.path.dirname(self.statefile))
        with open(self.statefile, 'w') as outf:
            json.dump(self._data, outf, indent=4, sort_keys=True)

    def clear(self):
        if os.path.exists(self.statefile):
            os.unlink(self.statefile)
        self._read()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.write()

    # helper function for creating properties. pylint: disable=protected-access
    def _prop(option):  # pylint: disable=no-self-argument
        def setprop(self, value):
            self._data[option] = value

        def getprop(self):
            return self._data.get(option)
        return property(getprop, setprop)

    #  !!! Increase STATE_VERSION for any changes in data structure like a new property or a new
    #  data structure !!!
    state_version = _prop("state_version")
    download_status = _prop("download_status")
    destdir = _prop("destdir")
    target_releasever = _prop("target_releasever")
    system_releasever = _prop("system_releasever")
    gpgcheck = _prop("gpgcheck")
    # list of repos with gpgcheck=True
    gpgcheck_repos = _prop("gpgcheck_repos")
    # list of repos with repo_gpgcheck=True
    repo_gpgcheck_repos = _prop("repo_gpgcheck_repos")
    upgrade_status = _prop("upgrade_status")
    upgrade_command = _prop("upgrade_command")
    distro_sync = _prop("distro_sync")
    poweroff_after = _prop("poweroff_after")
    enable_disable_repos = _prop("enable_disable_repos")
    module_platform_id = _prop("module_platform_id")

# --- Plymouth output helpers -------------------------------------------------


class PlymouthOutput(object):
    """A plymouth output helper class.

    Filters duplicate calls, and stops calling the plymouth binary if we
    fail to contact it.
    """

    def __init__(self):
        self.alive = True
        self._last_args = dict()
        self._last_msg = None

    def _plymouth(self, cmd, *args):
        dupe_cmd = (args == self._last_args.get(cmd))
        if (self.alive and not dupe_cmd) or cmd == '--ping':
            try:
                self.alive = (call((PLYMOUTH, cmd) + args) == 0)
            except OSError:
                self.alive = False
            self._last_args[cmd] = args
        return self.alive

    def ping(self):
        return self._plymouth("--ping")

    def message(self, msg):
        if self._last_msg and self._last_msg != msg:
            self._plymouth("hide-message", "--text", self._last_msg)
        self._last_msg = msg
        return self._plymouth("display-message", "--text", msg)

    def set_mode(self):
        mode = 'updates'
        try:
            s = check_output([PLYMOUTH, '--help'])
            if re.search('--system-upgrade', ucd(s)):
                mode = 'system-upgrade'
        except (CalledProcessError, OSError):
            pass
        return self._plymouth("change-mode", "--" + mode)

    def progress(self, percent):
        return self._plymouth("system-update", "--progress", str(percent))


# A single PlymouthOutput instance for us to use within this module
Plymouth = PlymouthOutput()


# A TransactionProgress class that updates plymouth for us.
class PlymouthTransactionProgress(dnf.callback.TransactionProgress):

    # pylint: disable=too-many-arguments
    def progress(self, package, action, ti_done, ti_total, ts_done, ts_total):
        self._update_plymouth(package, action, ts_done, ts_total)

    def _update_plymouth(self, package, action, current, total):
        # Prevents quick jumps of progressbar when pretrans scriptlets
        # and TRANS_PREPARATION are reported as 1/1
        if total == 1:
            return
        # Verification goes through all the packages again,
        # which resets the "current" param value, this prevents
        # resetting of the progress bar as well. (Rhbug:1809096)
        if action != dnf.callback.PKG_VERIFY:
            Plymouth.progress(int(90.0 * current / total))
        else:
            Plymouth.progress(90 + int(10.0 * current / total))

        Plymouth.message(self._fmt_event(package, action, current, total))

    def _fmt_event(self, package, action, current, total):
        action = dnf.transaction.ACTIONS.get(action, action)
        return "[%d/%d] %s %s..." % (current, total, action, package)

# --- journal helpers -------------------------------------------------


def find_boots(message_id):
    """Find all boots with this message id.

    Returns the entries of all found boots.
    """
    j = journal.Reader()
    j.add_match(MESSAGE_ID=message_id.hex,  # identify the message
                _UID=0)                     # prevent spoofing of logs

    oldboot = None
    for entry in j:
        boot = entry['_BOOT_ID']
        if boot == oldboot:
            continue
        oldboot = boot
        yield entry


def list_logs():
    print(_('The following boots appear to contain upgrade logs:'))
    n = -1
    for n, entry in enumerate(find_boots(ID_TO_IDENTIFY_BOOTS)):
        print('{} / {.hex}: {:%Y-%m-%d %H:%M:%S} {}→{}'.format(
            n + 1,
            entry['_BOOT_ID'],
            entry['__REALTIME_TIMESTAMP'],
            entry.get('SYSTEM_RELEASEVER', '??'),
            entry.get('TARGET_RELEASEVER', '??')))
    if n == -1:
        print(_('-- no logs were found --'))


def pick_boot(message_id, n):
    boots = list(find_boots(message_id))
    # Positive indices index all found boots starting with 1 and going forward,
    # zero is the current boot, and -1, -2, -3 are previous going backwards.
    # This is the same as journalctl.
    try:
        if n == 0:
            raise IndexError
        if n > 0:
            n -= 1
        return boots[n]['_BOOT_ID']
    except IndexError:
        raise CliError(_("Cannot find logs with this index."))


def show_log(n):
    boot_id = pick_boot(ID_TO_IDENTIFY_BOOTS, n)
    process = Popen(['journalctl', '--boot', boot_id.hex])
    process.wait()
    rc = process.returncode
    if rc == 1:
        raise dnf.exceptions.Error(_("Unable to match systemd journal entry"))


CMDS = ['download', 'clean', 'reboot', 'upgrade', 'log']

# --- The actual Plugin and Command objects! ----------------------------------


class SystemUpgradePlugin(dnf.Plugin):
    name = 'system-upgrade'

    def __init__(self, base, cli):
        super(SystemUpgradePlugin, self).__init__(base, cli)
        if cli:
            cli.register_command(SystemUpgradeCommand)
            cli.register_command(OfflineUpgradeCommand)
            cli.register_command(OfflineDistrosyncCommand)


class SystemUpgradeCommand(dnf.cli.Command):
    aliases = ('system-upgrade', 'fedup',)
    summary = _("Prepare system for upgrade to a new release")

    DATADIR = 'var/lib/dnf/system-upgrade'

    def __init__(self, cli):
        super(SystemUpgradeCommand, self).__init__(cli)
        self.datadir = os.path.join(cli.base.conf.installroot, self.DATADIR)
        self.transaction_file = os.path.join(self.datadir, 'system-upgrade-transaction.json')
        self.magic_symlink = os.path.join(cli.base.conf.installroot, 'system-update')

        self.state = State(os.path.join(self.datadir, 'system-upgrade-state.json'))

    @staticmethod
    def set_argparser(parser):
        parser.add_argument("--no-downgrade", dest='distro_sync',
                            action='store_false',
                            help=_("keep installed packages if the new "
                                   "release's version is older"))
        parser.add_argument('--poweroff', dest='poweroff_after',
                            action='store_true',
                            help=_("power off system after the operation "
                                   "is completed"))
        parser.add_argument('tid', nargs=1, choices=CMDS,
                            metavar="[%s]" % "|".join(CMDS))
        parser.add_argument('--number', type=int, help=_('which logs to show'))

    def log_status(self, message, message_id):
        """Log directly to the journal."""
        journal.send(message,
                     MESSAGE_ID=message_id,
                     PRIORITY=journal.LOG_NOTICE,
                     SYSTEM_RELEASEVER=self.state.system_releasever,
                     TARGET_RELEASEVER=self.state.target_releasever,
                     DNF_VERSION=dnf.const.VERSION)

    def pre_configure(self):
        self._call_sub("check")
        self._call_sub("pre_configure")

    def configure(self):
        self._call_sub("configure")

    def run(self):
        self._call_sub("run")

    def run_transaction(self):
        self._call_sub("transaction")

    def run_resolved(self):
        self._call_sub("resolved")

    def _call_sub(self, name):
        subfunc = getattr(self, name + '_' + self.opts.tid[0], None)
        if callable(subfunc):
            subfunc()

    def _check_state_version(self, command):
        if self.state.state_version != STATE_VERSION:
            msg = _("Incompatible version of data. Rerun 'dnf {command} download [OPTIONS]'"
                    "").format(command=command)
            raise CliError(msg)

    def _set_cachedir(self):
        # set download directories from json state file
        self.base.conf.cachedir = self.datadir
        self.base.conf.destdir = self.state.destdir if self.state.destdir else None

    def _get_forward_reverse_pkg_reason_pairs(self):
        """
        forward = {repoid:{pkg_nevra: {tsi.action: tsi.reason}}
        reverse = {pkg_nevra: {tsi.action: tsi.reason}}
        :return: forward, reverse
        """
        backward_action = set(dnf.transaction.BACKWARD_ACTIONS + [libdnf.transaction.TransactionItemAction_REINSTALLED])
        forward_actions = set(dnf.transaction.FORWARD_ACTIONS)

        forward = {}
        reverse = {}
        for tsi in self.cli.base.transaction:
            if tsi.action in forward_actions:
                pkg = tsi.pkg
                forward.setdefault(pkg.repo.id, {}).setdefault(
                    str(pkg), {})[tsi.action] = tsi.reason
            elif tsi.action in backward_action:
                reverse.setdefault(str(tsi.pkg), {})[tsi.action] = tsi.reason
        return forward, reverse

    # == pre_configure_*: set up action-specific demands ==========================
    def pre_configure_download(self):
        # only download subcommand accepts --destdir command line option
        self.base.conf.cachedir = self.datadir
        self.base.conf.destdir = self.opts.destdir if self.opts.destdir else None
        if 'offline-distrosync' == self.opts.command and not self.opts.distro_sync:
            raise CliError(
                _("Command 'offline-distrosync' cannot be used with --no-downgrade option"))
        elif 'offline-upgrade' == self.opts.command:
            self.opts.distro_sync = False

    def pre_configure_reboot(self):
        self._set_cachedir()

    def pre_configure_upgrade(self):
        self._set_cachedir()
        if self.state.enable_disable_repos:
            self.opts.repos_ed = self.state.enable_disable_repos
        self.base.conf.releasever = self.state.target_releasever

    def pre_configure_clean(self):
        self._set_cachedir()

    # == configure_*: set up action-specific demands ==========================

    def configure_download(self):
        if 'system-upgrade' == self.opts.command or 'fedup' == self.opts.command:
            logger.warning(_('WARNING: this operation is not supported on the RHEL distribution. '
                             'Proceed at your own risk.'))
            help_url = get_url_from_os_release()
            if help_url:
                msg = _('Additional information for System Upgrade: {}')
                logger.info(msg.format(ucd(help_url)))
            if self.base._promptWanted():
                msg = _('Before you continue ensure that your system is fully upgraded by running '
                        '"dnf --refresh upgrade". Do you want to continue')
                if self.base.conf.assumeno or not self.base.output.userconfirm(
                        msg='{} [y/N]: '.format(msg), defaultyes_msg='{} [Y/n]: '.format(msg)):
                    logger.error(_("Operation aborted."))
                    sys.exit(1)
            check_release_ver(self.base.conf, target=self.opts.releasever)
        elif 'offline-upgrade' == self.opts.command:
            self.cli._populate_update_security_filter(self.opts)

        self.cli.demands.root_user = True
        self.cli.demands.resolving = True
        self.cli.demands.available_repos = True
        self.cli.demands.sack_activation = True
        self.cli.demands.freshest_metadata = True
        # We want to do the depsolve / download / transaction-test, but *not*
        # run the actual RPM transaction to install the downloaded packages.
        # Setting the "test" flag makes the RPM transaction a test transaction,
        # so nothing actually gets installed.
        # (It also means that we run two test transactions in a row, which is
        # kind of silly, but that's something for DNF to fix...)
        self.base.conf.tsflags += ["test"]

    def configure_reboot(self):
        # FUTURE: add a --debug-shell option to enable debug shell:
        # systemctl add-wants system-update.target debug-shell.service
        self.cli.demands.root_user = True

    def configure_upgrade(self):
        # same as the download, but offline and non-interactive. so...
        self.cli.demands.root_user = True
        self.cli.demands.resolving = True
        self.cli.demands.available_repos = True
        self.cli.demands.sack_activation = True
        # use the saved value for --allowerasing, etc.
        self.opts.distro_sync = self.state.distro_sync
        if self.state.gpgcheck is not None:
            self.base.conf.gpgcheck = self.state.gpgcheck
        if self.state.gpgcheck_repos is not None:
            for repo in self.base.repos.values():
                repo.gpgcheck = repo.id in self.state.gpgcheck_repos
        if self.state.repo_gpgcheck_repos is not None:
            for repo in self.base.repos.values():
                repo.repo_gpgcheck = repo.id in self.state.repo_gpgcheck_repos
        self.base.conf.module_platform_id = self.state.module_platform_id
        # don't try to get new metadata, 'cuz we're offline
        self.cli.demands.cacheonly = True
        # and don't ask any questions (we confirmed all this beforehand)
        self.base.conf.assumeyes = True
        self.cli.demands.transaction_display = PlymouthTransactionProgress()
        # upgrade operation already removes all element that must be removed. Additional removal
        # could trigger unwanted changes in transaction.
        self.base.conf.clean_requirements_on_remove = False
        self.base.conf.install_weak_deps = False

    def configure_clean(self):
        self.cli.demands.root_user = True

    def configure_log(self):
        pass

    # == check_*: do any action-specific checks ===============================

    def check_reboot(self):
        if not self.state.download_status == 'complete':
            raise CliError(_("system is not ready for upgrade"))
        self._check_state_version(self.opts.command)
        if self.state.upgrade_command != self.opts.command:
            msg = _("the transaction was not prepared for '{command}'. "
                    "Rerun 'dnf {command} download [OPTIONS]'").format(command=self.opts.command)
            raise CliError(msg)
        if os.path.lexists(self.magic_symlink):
            raise CliError(_("upgrade is already scheduled"))
        dnf.util.ensure_dir(self.datadir)
        # FUTURE: checkRPMDBStatus(self.state.download_transaction_id)

    def check_upgrade(self):
        if not os.path.lexists(self.magic_symlink):
            logger.info(_("trigger file does not exist. exiting quietly."))
            raise SystemExit(0)
        if os.readlink(self.magic_symlink) != self.datadir:
            logger.info(_("another upgrade tool is running. exiting quietly."))
            raise SystemExit(0)
        # Delete symlink ASAP to avoid reboot loops
        dnf.yum.misc.unlink_f(self.magic_symlink)
        command = self.state.upgrade_command
        if not command:
            command = self.opts.command
        self._check_state_version(command)
        if not self.state.upgrade_status == 'ready':
            msg = _("use 'dnf {command} reboot' to begin the upgrade").format(command=command)
            raise CliError(msg)

    # == run_*: run the action/prep the transaction ===========================

    def run_prepare(self):
        # make the magic symlink
        os.symlink(self.datadir, self.magic_symlink)
        # set upgrade_status so that the upgrade can run
        with self.state as state:
            state.upgrade_status = 'ready'

    def run_reboot(self):
        self.run_prepare()

        if not self.opts.tid[0] == "reboot":
            return

        self.state.poweroff_after = self.opts.poweroff_after

        self.log_status(_("Rebooting to perform upgrade."),
                        REBOOT_REQUESTED_ID)

        # Explicit write since __exit__ doesn't seem to get called when rebooting
        self.state.write()
        reboot()

    def run_download(self):
        # Mark everything in the world for upgrade/sync
        if self.opts.distro_sync:
            self.base.distro_sync()
        else:
            self.base.upgrade_all()

        if self.opts.command not in ['offline-upgrade', 'offline-distrosync']:
            # Mark all installed groups and environments for upgrade
            self.base.read_comps()
            installed_groups = [g.id for g in self.base.comps.groups if self.base.history.group.get(g.id)]
            if installed_groups:
                self.base.env_group_upgrade(installed_groups)
            installed_environments = [g.id for g in self.base.comps.environments if self.base.history.env.get(g.id)]
            if installed_environments:
                self.base.env_group_upgrade(installed_environments)

        with self.state as state:
            state.download_status = 'downloading'
            state.target_releasever = self.base.conf.releasever
            state.destdir = self.base.conf.destdir

    def run_upgrade(self):
        # change the upgrade status (so we can detect crashed upgrades later)
        command = ''
        with self.state as state:
            state.upgrade_status = 'incomplete'
            command = state.upgrade_command
        if command == 'offline-upgrade':
            msg = _("Starting offline upgrade. This will take a while.")
        elif command == 'offline-distrosync':
            msg = _("Starting offline distrosync. This will take a while.")
        else:
            msg = _("Starting system upgrade. This will take a while.")

        self.log_status(msg, UPGRADE_STARTED_ID)

        # reset the splash mode and let the user know we're running
        Plymouth.set_mode()
        Plymouth.progress(0)
        Plymouth.message(msg)

        # disable screen blanking
        disable_blanking()

        self.replay = TransactionReplay(self.base, self.transaction_file)
        self.replay.run()

    def run_clean(self):
        logger.info(_("Cleaning up downloaded data..."))
        # Don't delete persistor, it contains paths for downloaded packages
        # that are used by dnf during finalizing base to clean them up
        clear_dir(self.base.conf.cachedir,
                  [dnf.persistor.TempfilePersistor(self.base.conf.cachedir).db_path])
        with self.state as state:
            state.download_status = None
            state.state_version = None
            state.upgrade_status = None
            state.upgrade_command = None
            state.destdir = None

    def run_log(self):
        if self.opts.number:
            show_log(self.opts.number)
        else:
            list_logs()

    # == resolved_*: do staff after succesful resolvement =====================

    def resolved_upgrade(self):
        """Adjust transaction reasons according to stored values"""
        self.replay.post_transaction()

    # == transaction_*: do stuff after a successful transaction ===============

    def transaction_download(self):
        transaction = self.base.history.get_current()

        if not transaction.packages():
            logger.info(_("The system-upgrade transaction is empty, your system is already up-to-date."))
            return

        data = serialize_transaction(transaction)
        try:
            with open(self.transaction_file, "w") as f:
                json.dump(data, f, indent=4, sort_keys=True)
                f.write("\n")

            print(_("Transaction saved to {}.").format(self.transaction_file))

        except OSError as e:
            raise dnf.cli.CliError(_('Error storing transaction: {}').format(str(e)))

        # Okay! Write out the state so the upgrade can use it.
        system_ver = dnf.rpm.detect_releasever(self.base.conf.installroot)
        with self.state as state:
            state.download_status = 'complete'
            state.state_version = STATE_VERSION
            state.distro_sync = self.opts.distro_sync
            state.gpgcheck = self.base.conf.gpgcheck
            state.gpgcheck_repos = [
                repo.id for repo in self.base.repos.values() if repo.gpgcheck]
            state.repo_gpgcheck_repos = [
                repo.id for repo in self.base.repos.values() if repo.repo_gpgcheck]
            state.system_releasever = system_ver
            state.target_releasever = self.base.conf.releasever
            state.module_platform_id = self.base.conf.module_platform_id
            state.enable_disable_repos = self.opts.repos_ed
            state.destdir = self.base.conf.destdir
            state.upgrade_command = self.opts.command

        msg = DOWNLOAD_FINISHED_MSG.format(command=self.opts.command)
        logger.info(msg)
        self.log_status(_("Download finished."), DOWNLOAD_FINISHED_ID)

    def transaction_upgrade(self):
        if self.state.poweroff_after:
            upgrade_complete_msg = _("Upgrade complete! Cleaning up and powering off...")
        else:
            upgrade_complete_msg = _("Upgrade complete! Cleaning up and rebooting...")

        Plymouth.message(upgrade_complete_msg)
        self.log_status(upgrade_complete_msg, UPGRADE_FINISHED_ID)

        self.run_clean()
        if self.opts.tid[0] == "upgrade":
            reboot(self.state.poweroff_after)


class OfflineUpgradeCommand(SystemUpgradeCommand):
    aliases = ('offline-upgrade',)
    summary = _("Prepare offline upgrade of the system")


class OfflineDistrosyncCommand(SystemUpgradeCommand):
    aliases = ('offline-distrosync',)
    summary = _("Prepare offline distrosync of the system")
