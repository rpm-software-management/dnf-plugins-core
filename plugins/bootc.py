# bootc.py, implements the 'bootc' command
#
# Copyright David Cantrell <dcantrell@redhat.com>
# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import absolute_import
from __future__ import unicode_literals

import dnf
import logging
import subprocess

_, P_ = dnf.i18n.translation("dnf-plugin-bootc")
logger = logging.getLogger("dnf.plugin")
rpm_logger = logging.getLogger("dnf.rpm")


@dnf.plugin.register_command
class BootcCommand(dnf.cli.Command):
    aliases = ["bootc"]
    summary = _("Modify software on a bootc-based system")
    usage = _("[PACKAGE ...]")

    _BOOTC_ALIASES = {"update": "upgrade", "erase": "remove"}
    _BOOTC_SUBCMDS = ["status"]
    _BOOTC_SUBCMDS_PKGSPECS = ["install"]
    _BOOTC_SUBCMDS_ALL = _BOOTC_SUBCMDS + _BOOTC_SUBCMDS_PKGSPECS

    _EXT_CMD = "rpm-ostree"

    def __init__(self, cli):
        super().__init__(cli)

    @staticmethod
    def set_argparser(parser):
        # subcommands for the plugin
        parser.add_argument(
            "subcmd",
            nargs=1,
            choices=BootcCommand._BOOTC_SUBCMDS_ALL,
            help=_("Available subcommands"),
        )

        # these options are for 'status'
        parser.add_argument(
            "--json", action="store_true", help=_("Output JSON (status)")
        )
        parser.add_argument(
            "--booted",
            action="store_true",
            help=_("Only print the booted deployment (status)"),
        )
        parser.add_argument(
            "--jsonpath",
            metavar="EXPRESSION",
            action="store",
            help=_("Filter JSONPath expression (status)"),
        )
        parser.add_argument(
            "--pending-exit-77",
            action="store_true",
            help=_("If pending deployment available, exit 77 (status)"),
        )

        # these options are for 'install'
        parser.add_argument(
            "--uninstall",
            nargs="+",
            metavar="PKG",
            action="store",
            help=_("Remove overlayed additional package (install)"),
        )
        parser.add_argument(
            "-A",
            "--apply-live",
            action="store_true",
            help=_(
                "Apply changes to both pending deployment and running filesystem tree (install)"
            ),
        )
        parser.add_argument(
            "--force-replacefiles",
            action="store_true",
            help=_("Allow package to replace files from other packages (install)"),
        )
        parser.add_argument(
            "-r",
            "--reboot",
            action="store_true",
            help=_("Initiate a reboot after operation is complete (install)"),
        )
        parser.add_argument(
            "--allow-inactive",
            action="store_true",
            help=_("Allow inactive package requests (install)"),
        )
        parser.add_argument(
            "--idempotent",
            action="store_true",
            help=_("Do nothing if package already (un)installed (install)"),
        )
        parser.add_argument(
            "--unchanged-exit-77",
            action="store_true",
            help=_("If no overlays were changed, exit 77 (install)"),
        )

        # valid under multiple subcommands
        parser.add_argument(
            "--peer",
            action="store_true",
            help=_(
                "Force a peer-to-peer connection instead of using the system message bus (status, install)"
            ),
        )

        parser.add_argument(
            "pkgspec", nargs="*", help=_("One or more package specifications")
        )

    def configure(self):
        super().configure()

        if self.opts.subcmd[0] in self._BOOTC_ALIASES.keys():
            cmd = self._BOOTC_ALIASES[self.opts.subcmd[0]]
        else:
            cmd = self.opts.subcmd[0]

        self.extargs = [self._EXT_CMD, cmd]

        # process subcommand arguments
        if cmd == "status":
            if self.opts.quiet:
                self.extargs.append("-q")
            elif self.opts.verbose:
                self.extargs.append("-v")
            elif self.opts.json:
                self.extargs.append("--json")
            elif self.opts.jsonpath:
                self.extargs.append("--jsonpath=%s" % self.opts.jsonpath)
            elif self.opts.booted:
                self.extargs.append("-b")
            elif self.opts.pending_exit_77:
                self.extargs.append("--pending-exit-77")
            elif self.opts.peer:
                self.extargs.append("--peer")
            elif self.opts.installroot:
                self.extargs.append("--sysroot=%s" % self.opts.installroot)
        elif cmd == "install":
            if self.opts.quiet:
                self.extargs.append("-q")
            elif self.opts.installroot:
                self.extargs.append("--sysroot=%s" % self.opts.installroot)
            elif self.opts.peer:
                self.extargs.append("--peer")
            elif self.opts.assumeyes:
                self.extargs.append("-y")
            elif self.opts.assumeno:
                self.extargs.append("-n")
            elif self.opts.cacheonly:
                self.extargs.append("-C")
            elif self.opts.downloadonly:
                self.extargs.append("--download-only")
            elif self.opts.releasever:
                self.extargs.append
                self.extargs.append("--releasever=%s" % self.opts.releasever)
            elif len(self.opts.repos_ed) > 0:
                enabled = set()
                disabled = set()

                for name, state in self.opts.repos_ed:
                    if state == "enable":
                        enabled.add(name)
                    elif state == "disable":
                        disabled.add(name)

                if len(list(enabled)) > 0:
                    for repo in list(enabled):
                        self.extargs.append("--enablerepo=%s" % repo)

                if len(list(disabled)) > 0:
                    for repo in list(disabled):
                        self.extargs.append("--disablerepo=%s" % repo)
            elif self.opts.uninstall:
                for pname in self.opts.uninstall:
                    self.extargs.append("--uninstall=%s" % pname)
            elif self.opts.apply_live:
                self.extargs.append("-A")
            elif self.opts.force_replacefiles:
                self.extargs.append("--force-replacefiles")
            elif self.opts.reboot:
                self.extargs.append("-r")
            elif self.opts.allow_inactive:
                self.extargs.append("--allow-inactive")
            elif self.opts.idempotent:
                self.extargs.append("--idempotent")
            elif self.opts.unchanged_exit_77:
                self.extargs.append("--unchanged-exit-77")

        if cmd in self._BOOTC_SUBCMDS_PKGSPECS:
            if self.opts.pkgspec is not None and len(self.opts.pkgspec) > 0:
                self.extargs += self.opts.pkgspec
            else:
                # ensure we have a valid subcommand
                logger.critical(
                    _("Missing package specification on bootc sub-command '%s'." % cmd)
                )
                raise dnf.cli.CliError

    def run(self):
        # combine stdout and stderr; capture text output
        proc = subprocess.Popen(
            self.extargs, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )

        # stdout and stderr will be combined in stdout, err will be None here
        (out, err) = proc.communicate()

        if proc.returncode != 0:
            logger.critical(out)
            raise dnf.cli.CliError
        else:
            logger.info(out)
