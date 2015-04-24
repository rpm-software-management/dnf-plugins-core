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
import dnfpluginscore.lib

class DebuginfoInstall(dnf.Plugin):
    """DNF plugin supplying the 'debuginfo-install' command."""

    name = 'debuginfo-install'

    def __init__(self, base, cli):
        """Initialize the plugin instance."""
        super(DebuginfoInstall, self).__init__(base, cli)
        if cli is not None:
            cli.register_command(DebuginfoInstallCommand)


class DebuginfoInstallCommand(dnf.cli.Command):
    """ DebuginfoInstall plugin for DNF """

    aliases = ("debuginfo-install",)
    summary = _('install debuginfo packages')
    usage = "[PACKAGE...]"

    srcdone = []
    reqdone = []
    packages = None
    packages_available = None
    packages_installed = None

    def configure(self, args):
        demands = self.cli.demands
        demands.resolving = True
        demands.root_user = True
        demands.sack_activation = True
        dnfpluginscore.lib.enable_debug_repos(self.base.repos)

    def run(self, args):
        self.packages = self.base.sack.query()
        self.packages_available = self.packages.available()
        self.packages_installed = self.packages.installed()

        for pkgspec in args:
            for pkg in dnf.subject.Subject(pkgspec).get_best_query(
                    self.cli.base.sack):
                self._di_install(pkg)

    @staticmethod
    def _pkgname_src(package):
        """get source package name without debuginfo suffix, e.g. krb5"""
        name = package.sourcerpm.replace("-{}.src.rpm".format(package.evr), "")
        # source package names usually do not contain epoch, handle both cases
        return name.replace("-{0.version}-{0.release}.src.rpm".format(package),
                            "")

    @classmethod
    def _pkgname_dbg(cls, package):
        """get source package name with debuginfo suffix, e.g. krb5-debuginfo"""
        srcname = cls._pkgname_src(package)
        assert "-debuginfo" not in srcname
        return "{}-debuginfo".format(srcname)

    def _dbg_available(self, package, match_evra):
        dbgname = self._pkgname_dbg(package)
        if match_evra:
            return self.packages_available.filter(
                name="{}".format(dbgname),
                epoch=int(package.epoch),
                version=str(package.version),
                release=str(package.release),
                arch=str(package.arch))
        else:
            return self.packages_available.filter(
                name="{}".format(dbgname),
                arch=str(package.arch))

    def _di_install(self, package):
        srcname = self._pkgname_src(package)
        dbgname = self._pkgname_dbg(package)
        if not srcname in self.srcdone:
            if self._dbg_available(package, True):
                di = "{0}-{1}:{2}-{3}.{4}".format(
                    dbgname,
                    package.epoch,
                    package.version,
                    package.release,
                    package.arch)
                self.base.install(di)
            elif self._dbg_available(package, False):
                di = "{0}.{1}".format(dbgname, package.arch)
                self.base.install(di)
            self.srcdone.append(srcname)

        if package.name in self.reqdone:
            return
        self.reqdone.append(package.name)
        for req in package.requires:
            if str(req).startswith("rpmlib("):
                continue
            elif str(req) in self.reqdone:
                continue
            elif str(req).find(".so") != -1:
                provides = self.packages_available.filter(provides=req)
                for p in provides:
                    if p.name in self.reqdone:
                        continue
                    pkgs = self.packages_installed.filter(name=p.name)
                    for dep in pkgs:
                        self._di_install(dep)
