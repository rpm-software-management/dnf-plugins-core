# debuginfo-install.py
# Install the debuginfo of packages and their dependencies to debug this package.
#
# Copyright (C) 2014 Igor Gnatenko
# Copyright (C) 2014-2019 Red Hat
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
from dnf.package import Package

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
            dbginfo = dnf.sack._rpmdb_sack(self.base).query().filterm(name__glob="*-debuginfo")
            if len(dbginfo):
                self.base.repos.enable_debug_repos()

class DebuginfoInstallCommand(dnf.cli.Command):
    """ DebuginfoInstall plugin for DNF """

    aliases = ("debuginfo-install",)
    summary = _('install debuginfo packages')

    def __init__(self, cli):
        super(DebuginfoInstallCommand, self).__init__(cli)

        self.available_debuginfo_missing = set()
        self.available_debugsource_missing = set()
        self.installed_debuginfo_missing = set()
        self.installed_debugsource_missing = set()

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
        errors_spec = []

        debuginfo_suffix_len = len(Package.DEBUGINFO_SUFFIX)
        debugsource_suffix_len = len(Package.DEBUGSOURCE_SUFFIX)

        for pkgspec in self.opts.package:
            solution = dnf.subject.Subject(pkgspec).get_best_solution(self.base.sack,
                                                                      with_src=False)

            query = solution["query"]
            if not query:
                logger.info(_('No match for argument: %s'), self.base.output.term.bold(pkgspec))
                errors_spec.append(pkgspec)
                continue

            package_dict = query.available()._name_dict()
            # installed versions of packages have priority, replace / add them to the dict
            package_dict.update(query.installed()._name_dict())

            # Remove debuginfo packages if their base packages are in the query.
            # They can get there through globs and they break the installation
            # of debug packages with the same version as the installed base
            # packages. If the base package of a debuginfo package is not in
            # the query, the user specified a debug package on the command
            # line. We don't want to ignore those, so we will install them.
            # But, in this case the version will not be matched to the
            # installed version of the base package, as that would require
            # another query and is further complicated if the user specifies a
            # version themselves etc.
            for name in list(package_dict.keys()):
                if name.endswith(Package.DEBUGINFO_SUFFIX):
                    if name[:-debuginfo_suffix_len] in package_dict:
                        package_dict.pop(name)
                if name.endswith(Package.DEBUGSOURCE_SUFFIX):
                    if name[:-debugsource_suffix_len] in package_dict:
                        package_dict.pop(name)

            # attempt to install debuginfo and debugsource for the highest
            # listed version of the package (in case the package is installed,
            # only the installed version is listed)
            for pkgs in package_dict.values():
                first_pkg = pkgs[0]

                # for packages from system (installed) there can be more
                # packages with different architectures listed and we want to
                # install debuginfo for all of them
                if first_pkg._from_system:
                    # we need to split them by architectures and install the
                    # latest version for each architecture
                    arch_dict = {}

                    for pkg in pkgs:
                        arch_dict.setdefault(pkg.arch, []).append(pkg)

                    for package_arch_list in arch_dict.values():
                        pkg = package_arch_list[0]

                        if not self._install_debug_from_system(pkg.debug_name, pkg):
                            if not self._install_debug_from_system(pkg.source_debug_name, pkg):
                                self.installed_debuginfo_missing.add(str(pkg))

                        if not self._install_debug_from_system(pkg.debugsource_name, pkg):
                            self.installed_debugsource_missing.add(str(pkg))

                    continue

                # if the package in question is -debuginfo or -debugsource, install it directly
                if first_pkg.name.endswith(Package.DEBUGINFO_SUFFIX) \
                        or first_pkg.name.endswith(Package.DEBUGSOURCE_SUFFIX):

                    self._install(pkgs)  # pass all pkgs to the solver, it will pick the best one
                    continue

                # if we have NEVRA parsed from the pkgspec, use it to install the package
                if solution["nevra"] is not None:
                    if not self._install_debug(first_pkg.debug_name, solution["nevra"]):
                        if not self._install_debug(first_pkg.source_debug_name, solution["nevra"]):
                            self.available_debuginfo_missing.add(
                                "{}-{}".format(first_pkg.name, first_pkg.evr))

                    if not self._install_debug(first_pkg.debugsource_name, solution["nevra"]):
                        self.available_debugsource_missing.add(
                            "{}-{}".format(first_pkg.name, first_pkg.evr))

                    continue

                # if we don't have NEVRA from the pkgspec, pass nevras from
                # all packages that were found (while replacing the name with
                # the -debuginfo and -debugsource variant) to the solver, which
                # will pick the correct version and architecture
                if not self._install_debug_no_nevra(first_pkg.debug_name, pkgs):
                    if not self._install_debug_no_nevra(first_pkg.source_debug_name, pkgs):
                        self.available_debuginfo_missing.add(
                            "{}-{}".format(first_pkg.name, first_pkg.evr))

                if not self._install_debug_no_nevra(first_pkg.debugsource_name, pkgs):
                    self.available_debugsource_missing.add(
                        "{}-{}".format(first_pkg.name, first_pkg.evr))

        if self.available_debuginfo_missing:
            logger.info(
                _("Could not find debuginfo package for the following available packages: %s"),
                ", ".join(sorted(self.available_debuginfo_missing)))

        if self.available_debugsource_missing:
            logger.info(
                _("Could not find debugsource package for the following available packages: %s"),
                ", ".join(sorted(self.available_debugsource_missing)))

        if self.installed_debuginfo_missing:
            logger.info(
                _("Could not find debuginfo package for the following installed packages: %s"),
                ", ".join(sorted(self.installed_debuginfo_missing)))

        if self.installed_debugsource_missing:
            logger.info(
                _("Could not find debugsource package for the following installed packages: %s"),
                ", ".join(sorted(self.installed_debugsource_missing)))

        if errors_spec and self.base.conf.strict:
            raise dnf.exceptions.PackagesNotAvailableError(_("Unable to find a match"),
                                                           pkg_spec=' '.join(errors_spec))

    def _install_debug_from_system(self, debug_name, pkg):
        query = self.base.sack.query().filter(name=debug_name,
                                              epoch=pkg.epoch,
                                              version=pkg.version,
                                              release=pkg.release,
                                              arch=pkg.arch)

        if query:
            self._install(query)
            return True

        return False

    def _install_debug(self, debug_name, base_nevra):
        kwargs = {}

        # if some part of EVRA was specified in the argument, add it as a filter
        if base_nevra.epoch is not None:
            kwargs["epoch__glob"] = base_nevra.epoch
        if base_nevra.version is not None:
            kwargs["version__glob"] = base_nevra.version
        if base_nevra.release is not None:
            kwargs["release__glob"] = base_nevra.release
        if base_nevra.arch is not None:
            kwargs["arch__glob"] = base_nevra.arch

        query = self.base.sack.query().filter(name=debug_name, **kwargs)

        if query:
            self._install(query)
            return True

        return False

    def _install_debug_no_nevra(self, debug_name, pkgs):
        query = self.base.sack.query().filterm(
            nevra_strict=["{}-{}.{}".format(debug_name, p.evr, p.arch) for p in pkgs])
        if query:
            self._install(query)
            return True

        return False

    def _install(self, pkgs):
        selector = dnf.selector.Selector(self.base.sack)
        selector.set(pkg=pkgs)
        self.base.goal.install(select=selector, optional=not self.base.conf.strict)
