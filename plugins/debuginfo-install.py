# debuginfo-install.py
# Install the debuginfo of packages and their dependencies to debug this package.
#
# Copyright (C) 2014 Igor Gnatenko
# Copyright (C) 2014 Red Hat
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details. You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA. Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#

from dnfpluginscore import _, logger

import dnf
import dnf.cli
import dnf.subject

class DebuginfoInstall(dnf.Plugin):
    """DNF plugin supplying the 'debuginfo-install' command."""

    name = 'debuginfo-install'

    def __init__(self, base, cli):
        """Initialize the plugin instance."""
        super(DebuginfoInstall, self).__init__(base, cli)
        self.base = base
        self.cli = cli
        if cli is not None:
            cli.register_command(DebuginfoInstallCommand)

    def config(self):
        cp = self.read_config(self.base.conf)
        autoupdate = (cp.has_section('main')
                      and cp.has_option('main', 'autoupdate')
                      and cp.getboolean('main', 'autoupdate'))

        if autoupdate:
            # allow update of already installed debuginfo packages
            dbginfo = dnf.sack._rpmdb_sack(self.base).query().filter(
                                                name__glob="*-debuginfo")
            if len(dbginfo):
                self.base.repos.enable_debug_repos()

class DebuginfoInstallCommand(dnf.cli.Command):
    """ DebuginfoInstall plugin for DNF """

    aliases = ("debuginfo-install",)
    summary = _('install debuginfo packages')

    dbgdone = []
    packages = None
    packages_available = None

    @staticmethod
    def set_argparser(parser):
        parser.add_argument('package', nargs='+')

    def configure(self):
        demands = self.cli.demands
        demands.resolving = True
        demands.root_user = True
        demands.sack_activation = True
        demands.available_repos = True
        self.base.repos.enable_debug_repos()

    def run(self):
        self.packages = self.base.sack.query()
        self.packages_available = self.packages.available()
        errors_spec = []

        for pkgspec in self.opts.package:
            package_query = sorted(dnf.subject.Subject(pkgspec).get_best_query(
                self.cli.base.sack).filter(arch__neq='src'), reverse=True)
            if not package_query:
                msg = _('No match for argument: %s')
                logger.info(msg, self.base.output.term.bold(pkgspec))
                errors_spec.append(pkgspec)
            for pkg in package_query:
                self._di_install(pkg)

        if not self.dbgdone:
            logger.info(_("No debuginfo packages available to install"))

        if errors_spec and self.base.conf.strict:
            raise dnf.exceptions.PackagesNotAvailableError(_("Unable to find a match"),
                                                           pkg_spec=' '.join(errors_spec))

    def _dbg_available(self, dbgname, package, match_evra):
        if match_evra:
            return self.packages_available.filter(
                name=dbgname,
                epoch=int(package.epoch),
                version=str(package.version),
                release=str(package.release),
                arch=str(package.arch))
        else:
            return self.packages_available.filter(
                name=dbgname,
                arch=str(package.arch))

    def _di_install(self, package):
        for dbgname in [package.debug_name, package.source_debug_name]:
            if dbgname in self.dbgdone:
                break
            if self._dbg_available(dbgname, package, True):
                di = "{0}-{1}:{2}-{3}.{4}".format(
                    dbgname,
                    package.epoch,
                    package.version,
                    package.release,
                    package.arch)
                self.base.install(di)
            elif self._dbg_available(dbgname, package, False):
                di = "{0}.{1}".format(dbgname, package.arch)
                self.base.install(di)
            else:
                continue
            self.dbgdone.append(dbgname)
            break
        else:
            logger.info(
                _("Could not find debuginfo for package: %s") % package)
