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

from dnf.i18n import plugins_ugettext as _
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
    activate_sack = True
    resolve = True
    writes_rpmdb = True

    def doCheck(self, basecmd, extcmds):
        """Verify that conditions are met so that this command can run."""
        dnf.cli.commands.checkGPGKey(self.base, self.cli)
        if len(extcmds) != 1:
            self.cli.logger.critical(
                _('Error: Requires exactly one path to a kickstart file'))
            dnf.cli.commands._err_mini_usage(self.cli, basecmd)
            raise dnf.cli.CliError('exactly one path to a kickstart file required')
        dnf.cli.commands.checkEnabledRepo(self.base, extcmds)

    @staticmethod
    def get_summary():
        """Return a one line summary of what the command does."""
        return _("Install packages defined in a kickstart file on your system")

    @staticmethod
    def get_usage():
        """Return a usage string for the command, including arguments."""
        return _("FILE")

    def run(self, extcmds):
        """Execute the command."""
        try:
            path, = extcmds
        except ValueError:
            raise ValueError('exactly one path to a kickstart file required')

        try:
            packages = parse_kickstart_packages(path)
        except pykickstart.errors.KickstartError as err:
            raise dnf.exceptions.Error(
                'the file cannot be parsed: {}'.format(err))
        group_names = [group.name for group in packages.groupList]

        if group_names:
            self.base.read_comps()
        try:
            self.base.install_grouplist(group_names)
        except dnf.exceptions.Error:
            are_groups_installed = False
        else:
            are_groups_installed = True
        try:
            self.base.installPkgs(packages.packageList)
        except dnf.exceptions.Error:
            are_packages_installed = False
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
