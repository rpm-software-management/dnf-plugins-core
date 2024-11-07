# bootc.py, implements the 'bootc' command
#
# Copyright David Cantrell <dcantrell@redhat.com>
# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import absolute_import
from __future__ import unicode_literals

import dnf
import logging
import subprocess
import sys

_, P_ = dnf.i18n.translation("dnf-plugin-bootc")
logger = logging.getLogger("dnf.plugin")
rpm_logger = logging.getLogger("dnf.rpm")


@dnf.plugin.register_command
class BootcCommand(dnf.cli.Command):
    aliases = ["bootc"]
    summary = _("Modify software on a bootc-based system")
    usage = _("[PACKAGE ...]")

    _BOOTC_ALIASES = {}
    _BOOTC_SUBCMDS = ["status"]
    _BOOTC_SUBCMDS_PKGSPECS = []
    _BOOTC_SUBCMDS_ALL = _BOOTC_SUBCMDS + _BOOTC_SUBCMDS_PKGSPECS

    _EXT_CMD = "bootc"

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
            "--format", choices=["humanreadable", "yaml", "json"], default="humanreadable", help=_("output format")
        )
        parser.add_argument(
            "--booted",
            action="store_true",
            help=_("Only print the booted deployment (status)"),
        )

        # valid under multiple subcommands
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
            self.extargs.extend(("--format-version", "1"))
            self.extargs.extend(("--format", self.opts.format))
            if self.opts.booted:
                self.extargs.append("-b")

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
        try:
            completed_process = subprocess.run(self.extargs, stdout=sys.stdout, stderr=sys.stderr)
            sys.exit(completed_process.returncode)
        except FileNotFoundError as e:
            raise dnf.cli.CliError(_("bootc command not found. Is this a bootc system?"))
