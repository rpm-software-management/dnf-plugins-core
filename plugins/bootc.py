# bootc.py, implements the 'bootc' command
#
# Copyright David Cantrell <dcantrell@redhat.com>
# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import absolute_import
from __future__ import unicode_literals

import dnf
import logging
import sys
import subprocess

_, P_ = dnf.i18n.translation("dnf-plugin-bootc")
logger = logging.getLogger("dnf.plugin")
rpm_logger = logging.getLogger("dnf.rpm")


@dnf.plugin.register_command
class BootcCommand(dnf.cli.Command):
    aliases = ["bootc"]
    summary = _("Modify software on a bootc-based system")

    _BOOTC_ALIASES = {"update": "upgrade", "erase": "remove"}
    _BOOTC_SUBCOMMANDS = ["status", "install"]

    _EXT_CMD = "rpm-ostree"

    def _canonical(self):
        if self.opts.subcmd is None:
            self.opts.subcmd = "status"

        if self.opts.subcmd in self._BOOTC_ALIASES.keys():
            self.opts.subcmd = self._BOOTC_ALIASES[self.opts.subcmd]

    def __init__(self, cli):
        super().__init__(cli)

    @staticmethod
    def set_argparser(parser):
        # subcommands for the plugin
        parser.add_argument(
            "subcmd",
            nargs="?",
            metavar="BOOTC",
            help=_("available subcommands: {} (default), {}").format(
                BootcCommand._BOOTC_SUBCOMMANDS[0],
                ", ".join(BootcCommand._BOOTC_SUBCOMMANDS[1:]),
            ),
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
        parser.add_argument(
            "--peer",
            action="store_true",
            help=_(
                "Force a peer-to-peer connection instead of using the system message bus (status)"
            ),
        )

    def configure(self):
        super().configure()

        self._canonical()
        cmd = self.opts.subcmd

        # ensure we have a valid subcommand
        if cmd not in self._BOOTC_SUBCOMMANDS:
            logger.critical(
                _("Invalid bootc sub-command, use: %s."),
                ", ".join(self._BOOTC_SUBCOMMANDS),
            )
            raise dnf.cli.CliError

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

    def run(self):
        proc = subprocess.Popen(
            self.extargs, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        output = proc.communicate()

        if proc.returncode != 0:
            logger.critical(output)
            raise dnf.cli.CliError
        else:
            logger.info(output)
