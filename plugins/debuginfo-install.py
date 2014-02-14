# debuginfo-install.py
# Install all the deps needed to build this package.
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

import dnf
import os
import rpm

from dnf.yum.i18n import _

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

    sack_activate = True
    aliases = ("debuginfo-install",)
    resolve = True

    def run(self, args):
        # FIXME this should do dnf itself (BZ#1062889)
        if os.geteuid() != 0:
            raise dnf.exceptions.Error(_('This command has to be run under the root user.'))
        self._enable_debug_repos()
        self.base.fill_sack()
        self.done = []
        self.packages = self.base.sack.query()
        self.packages_available = self.packages.available()
        self.packages_installed = self.packages.installed()
        for pkg in args:
            pkgs = self.packages_installed.filter(name=pkg)
            if not pkgs:
                pkgs = self.packages_available.filter(name=pkg)
            for pkg in pkgs:
                self._di_install(pkg)

    def _di_install(self, po):
        if po.name in self.done:
            return
        if "-debuginfo" in po.name:
            di = "{0}-{1}:{2}-{3}.{4}".format(po.name, po.epoch, po.version, po.release, po.arch)
        else:
            di = "{0}-debuginfo-{1}:{2}-{3}.{4}".format(po.name, po.epoch, po.version, po.release, po.arch)
        self.done.append(po.name)
        try:
            self.base.install(di)
        except dnf.exceptions.MarkingError:
            di = "{0}-debuginfo.{1}".format(po.name, po.arch)
            try:
                self.base.install(di)
            except dnf.exceptions.MarkingError:
                # FIXME:
                # libfreebl3.so()(64bit) pointing to nss-softokn-freebl
                # but we have only nss-softokn-debuginfo
                # Therefore temporary pass
                pass
        for req in po.requires:
            if str(req).startswith("rpmlib("):
                continue
            elif str(req).find(".so") != -1:
                provides = self.packages_available.filter(provides=req)
                for p in provides:
                    pkgs = self.packages_installed.filter(name=p.name)
                    if not pkgs:
                        pkgs = self.packages_installed.filter(name=p.name)
                    for pkg in pkgs:
                        self._di_install(p)

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
                    self.cli.logger.debug(_("enabling {}").format(id))
                    self.base.repos[r].enable()
