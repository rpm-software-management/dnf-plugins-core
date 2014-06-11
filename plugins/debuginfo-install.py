# debuginfo-install.py
# Install the debuginfo version of packages and their dependencies to debug this package.
#
# Copyright (C) 2014 Igor Gnatenko
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

from dnfpluginscore import _

import dnf
import dnf.cli


class DebuginfoInstall(dnf.Plugin):
    """DNF plugin supplying the 'debuginfo-install' command."""

    name = 'debuginfo-install'

    def __init__(self, base, cli):
        """Initialize the plugin instance."""
        super(DebuginfoInstall, self).__init__(base, cli)
        if cli is not None:
            cli.register_command(DebuginfoInstallCommand)
        cli.logger.debug("initialized DebuginfoInstall plugin")


class DebuginfoInstallCommand(dnf.cli.Command):
    """ DebuginfoInstall plugin for DNF """

    aliases = ("debuginfo-install",)
    summary = _('install debuginfo packages')
    usage = "[PACKAGE...]"

    def configure(self, args):
        demands = self.cli.demands
        demands.resolving = True
        demands.root_user = True
        demands.sack_activation = True

    def run(self, args):
        self._enable_debug_repos()
        self.base.fill_sack()
        self.done = []
        self.rejected = []
        self.packages = self.base.sack.query()
        self.packages_available = self.packages.available()
        self.packages_installed = self.packages.installed()
        for pkg in args:
            pkgs = self.packages_installed.filter(name=pkg)
            if not pkgs:
                pkgs = self.packages_available.filter(name=pkg)
            for pkg in pkgs:
                self._di_install(pkg, None)

    def _is_available(self, p, flag):
        if "-debuginfo" in p.name:
            name = p.name
        else:
            name = "{}-debuginfo".format(p.name)
        if flag:
            avail = self.packages_available.filter(
                name="{}".format(name),
                epoch=int(p.epoch),
                version=str(p.version),
                release=str(p.release),
                arch=str(p.arch))
        else:
            avail = self.packages_available.filter(
                name="{}".format(name),
                arch=str(p.arch))
        if len(avail) != 0:
            return self.packages_available.filter(
                name="{}".format(name.replace("-debuginfo", "")),
                epoch=int(p.epoch),
                version=str(p.version),
                release=str(p.release),
                arch=str(p.arch))
        else:
            return False

    def _di_install(self, po, r):
        if po.name in self.done or r in self.done or po in self.rejected:
            return
        if self._is_available(po, True):
            self.done.append(po.name)
            if r:
                self.done.append(r)
            if "-debuginfo" in po.name:
                di = "{0}-{1}:{2}-{3}.{4}".format(
                        po.name, po.epoch, po.version, po.release, po.arch)
            else:
                di = "{0}-debuginfo-{1}:{2}-{3}.{4}".format(
                        po.name, po.epoch, po.version, po.release, po.arch)
            self.base.install(di)
        else:
            if self._is_available(po, False):
                di = "{0}-debuginfo.{1}".format(po.name, po.arch)
                self.base.install(di)
                self.done.append(po.name)
                if r:
                    self.done.append(r)
            else:
                pass
        for req in po.requires:
            if str(req).startswith("rpmlib("):
                continue
            elif str(req) in self.done:
                continue
            elif str(req).find(".so") != -1:
                provides = self.packages_available.filter(provides=req)
                for p in provides:
                    if str(p.name) in self.done or p in self.rejected:
                        continue
                    pkgs = self.packages_installed.filter(name=p.name)
                    if len(pkgs) != 0:
                        pkgs_avail = self._is_available(p, True)
                        if not pkgs_avail:
                            for x in pkgs:
                                # FIXME:
                                # libfreebl3.so()(64bit) pointing to nss-softokn-freebl
                                # but we have only nss-softokn-debuginfo
                                self.cli.logger.debug(
                                        _("Can't find debuginfo package for: {0}-{1}:{2}-{3}.{4}").format(
                                            x.name, x.epoch, x.version, x.release, x.arch))
                                self.rejected.append(x)
                            pkgs = []
                        else:
                            pkgs = pkgs_avail
                    for pkg in pkgs:
                        self._di_install(pkg, str(req))

    def _enable_debug_repos(self):
        repos = {}
        for repo in self.base.repos.iter_enabled():
            repos[repo.id] = repo
        for repoid in repos:
            if repoid.endswith("-rpms"):
                di = repoid[:-5] + "-debug-rpms"
            else:
                di = "{}-debuginfo".format(repoid)
            if di in repos:
                continue
            repo = repos[repoid]
            for r in self.base.repos:
                if r == di:
                    self.cli.logger.debug(_("enabling {}").format(di))
                    self.base.repos[r].enable()
