# kickstart.py, supplies the 'kickstart' command.
#
# Copyright (C) 2013  Red Hat, Inc.
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

from __future__ import absolute_import
from __future__ import unicode_literals
from dnfpluginscore import _, logger

import dnf.cli
import pykickstart.parser


def parse_kickstart_packages(path):
    """Return content of packages sections in the kickstart file."""
    handler = pykickstart.version.makeVersion()
    parser = MaskableKickstartParser(handler)

    # Ignore all commands and sections except the packages.
    handler.maskAllExcept({})
    parser.mask_all({pykickstart.sections.PackageSection.sectionOpen})

    parser.readKickstart(path)

    return handler.packages


class Kickstart(dnf.Plugin):
    """DNF plugin supplying the kickstart command."""

    name = 'kickstart'

    def __init__(self, base, cli):
        """Initialize the plugin instance."""
        super(Kickstart, self).__init__(base, cli)
        if cli is not None:
            cli.register_command(KickstartCommand)


class KickstartCommand(dnf.cli.Command):
    """A command installing groups/packages defined in kickstart files."""

    aliases = ('kickstart',)
    summary = _("Install packages defined in a kickstart file on your system")
    usage = _("FILE")

    def doCheck(self, basecmd, extcmds):
        """Verify that conditions are met so that this command can run."""
        dnf.cli.commands.checkGPGKey(self.base, self.cli)
        try:
            self.parse_extcmds(extcmds)
        except ValueError:
            logger.critical(
                _('Error: Requires exactly one path to a kickstart file'))
            dnf.cli.commands.err_mini_usage(self.cli, basecmd)
            raise dnf.cli.CliError(
                _('exactly one path to a kickstart file required'))
        dnf.cli.commands.checkEnabledRepo(self.base, extcmds)

    @classmethod
    def parse_extcmds(cls, extcmds):
        """Parse command arguments *extcmds*."""
        path, = extcmds
        return path

    def configure(self, args):
        demands = self.cli.demands
        demands.resolving = True
        demands.root_user = True
        demands.sack_activation = True

    def run(self, extcmds):
        """Execute the command."""
        self.doCheck(self.base.basecmd, extcmds)

        path = self.parse_extcmds(extcmds)

        try:
            packages = parse_kickstart_packages(path)
        except pykickstart.errors.KickstartError:
            raise dnf.exceptions.Error(_('file cannot be parsed: %s') % path)
        group_names = [group.name for group in packages.groupList]

        if group_names:
            self.base.fill_sack()
            self.base.read_comps()
        try:
            for group in group_names:
                grp = self.base.comps.group_by_pattern(group)
                if grp:
                    self.base.group_install(grp, "default")
        except dnf.exceptions.Error:
            are_groups_installed = False
        else:
            are_groups_installed = True

        are_packages_installed = False
        for pattern in packages.packageList:
            try:
                self.base.install(pattern)
            except dnf.exceptions.MarkingError:
                logger.info(_('No package %s available.'), pattern)
            else:
                are_packages_installed = True

        if not are_groups_installed and not are_packages_installed:
            raise dnf.exceptions.Error(_('Nothing to do.'))


class MaskableKickstartParser(pykickstart.parser.KickstartParser):
    """Kickstart files parser able to ignore given sections."""

    def mask_all(self, section_exceptions=()):
        """Ignore all sections except the given sections."""
        null_class = pykickstart.sections.NullSection
        for section_open, _section in self._sections.items():
            if section_open not in section_exceptions:
                self.registerSection(
                    null_class(self.handler, sectionOpen=section_open))
