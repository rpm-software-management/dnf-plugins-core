# download.py, supplies the 'download' command.
#
# Copyright (C) 2013-2015  Red Hat, Inc.
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

import dnf
import dnf.cli
import dnf.exceptions
import dnf.i18n
import dnf.subject
import dnfpluginscore
import hawkey
import itertools
import os
import shutil


@dnf.plugin.register_command
class DownloadCommand(dnf.cli.Command):

    aliases = ['download']
    summary = _('Download package to current directory')

    def __init__(self, cli):
        super(DownloadCommand, self).__init__(cli)
        self.opts = None
        self.parser = None

    @staticmethod
    def set_argparser(parser):
        parser.add_argument('packages', nargs='+',
                            help=_('packages to download'))
        target = parser.add_mutually_exclusive_group()
        target.add_argument("--source", action='store_true',
                            help=_('download the src.rpm instead'))
        target.add_argument("--debuginfo", action='store_true',
                            help=_('download the -debuginfo package instead'))
        parser.add_argument('--destdir',
                            help=_('download path, default is current dir'))
        parser.add_argument('--resolve', action='store_true',
                            help=_('resolve and download needed dependencies'))

    def configure(self):
        # setup sack and populate it with enabled repos
        demands = self.cli.demands
        demands.sack_activation = True
        demands.available_repos = True

        if self.opts.source:
            dnfpluginscore.lib.enable_source_repos(self.base.repos)

        if self.opts.debuginfo:
            dnfpluginscore.lib.enable_debug_repos(self.base.repos)

    def run(self):
        """Execute the util action here."""

        if self.opts.source:
            locations = self._download_source(self.opts.packages)
        elif self.opts.debuginfo:
            locations = self._download_debuginfo(self.opts.packages)
        else:
            locations = self._download_rpms(self.opts.packages)

        if self.opts.destdir:
            dest = self.opts.destdir
        else:
            dest = dnf.i18n.ucd(os.getcwd())

        self._copy_packages(dest, locations)

    def _download_rpms(self, pkg_specs):
        """Download packages to dnf cache."""
        if self.opts.resolve:
            pkgs = self._get_packages_with_deps(pkg_specs)
        else:
            pkgs = self._get_packages(pkg_specs)
        self.base.download_packages(pkgs, self.base.output.progress)
        locations = sorted([pkg.localPkg() for pkg in pkgs])
        return locations

    def _download_source(self, pkg_specs):
        """Download source packages to dnf cache."""
        pkgs = self._get_packages(pkg_specs)
        source_pkgs = self._get_source_packages(pkgs)
        pkgs = set(self._get_packages(source_pkgs, source=True))
        self.base.download_packages(pkgs, self.base.output.progress)
        locations = sorted([pkg.localPkg() for pkg in pkgs])
        return locations

    def _download_debuginfo(self, pkg_specs):
        """Download debuginfo packages to dnf cache."""
        dbg_pkgs = set()
        q = self.base.sack.query()
        q = q.available()

        for pkg in self._get_packages(pkg_specs):
            for dbg_name in [dnfpluginscore.lib.package_debug_name(pkg),
                            dnfpluginscore.lib.package_source_debug_name(pkg)]:
                dbg_available = q.filter(
                                        name=dbg_name,
                                        epoch=int(pkg.epoch),
                                        version=pkg.version,
                                        release=pkg.release,
                                        arch=pkg.arch
                                    )
                dbg_found = False
                for p in dbg_available:
                    dbg_pkgs.add(p)
                    dbg_found = True

                if dbg_found:
                    break

        self.base.download_packages(dbg_pkgs, self.base.output.progress)
        locations = sorted([pkg.localPkg() for pkg in dbg_pkgs])
        return locations

    def _get_packages(self, pkg_specs, source=False):
        """Get packages matching pkg_specs."""
        func = self._get_query_source if source else self._get_query
        queries = []
        for pkg_spec in pkg_specs:
            try:
                queries.append(func(pkg_spec))
            except dnf.exceptions.PackageNotFoundError as e:
                logger.error(dnf.i18n.ucd(e))
                if self.base.conf.strict:
                    logger.error(_("Exiting due to strict setting."))
                    raise dnf.exceptions.Error(e)

        pkgs = list(itertools.chain(*queries))
        return pkgs

    def _get_packages_with_deps(self, pkg_specs, source=False):
        """Get packages matching pkg_specs and the deps."""
        pkgs = self._get_packages(pkg_specs)
        goal = hawkey.Goal(self.base.sack)
        for pkg in pkgs:
            goal.install(pkg)
        rc = goal.run()
        if rc:
            pkgs = goal.list_installs()
            return pkgs
        else:
            logger.debug(_('Error in resolve'))
            return []

    @staticmethod
    def _get_source_packages(pkgs):
        """Get list of source rpm names for a list of packages."""
        source_pkgs = set()
        for pkg in pkgs:
            if pkg.sourcerpm:
                source_pkgs.add(pkg.sourcerpm)
                logger.debug('  --> Package : %s Source : %s',
                             str(pkg), pkg.sourcerpm)
            elif pkg.arch == 'src':
                source_pkgs.add("%s-%s.src.rpm" % (pkg.name, pkg.evr))
            else:
                logger.info(_("No source rpm defined for %s"), str(pkg))
        return list(source_pkgs)

    def _get_query(self, pkg_spec):
        """Return a query to match a pkg_spec."""
        if os.path.exists(pkg_spec):
            pkgs = self.base.add_remote_rpms([pkg_spec])
            pkg_spec = "{0.name}-{0.epoch}:{0.version}-{0.release}.{0.arch}".format(pkgs[0])

        subj = dnf.subject.Subject(pkg_spec)
        q = subj.get_best_query(self.base.sack)
        q = q.available()
        q = q.latest()
        if len(q.run()) == 0:
            msg = _("No package ") + pkg_spec + _(" available.")
            raise dnf.exceptions.PackageNotFoundError(msg)
        return q

    def _get_query_source(self, pkg_spec):
        """Return a query to match a source rpm file name."""
        pkg_spec = pkg_spec[:-4]  # skip the .rpm
        nevra = hawkey.split_nevra(pkg_spec)
        q = self.base.sack.query()
        q = q.available()
        q = q.latest()
        q = q.filter(name=nevra.name, version=nevra.version,
                     release=nevra.release, arch=nevra.arch)
        if len(q.run()) == 0:
            msg = _("No package ") + pkg_spec + _(" available.")
            raise dnf.exceptions.PackageNotFoundError(msg)
        return q

    @staticmethod
    def _copy_packages(target, locations):
        """Copy the downloaded package to target, not move.
           If package is from local repo it must not be deleted there
           and download routines will remove them from cache automatically.
        """
        if not os.path.exists(target):
            os.makedirs(target)
        for pkg in locations:
            shutil.copy(pkg, target)
        return target
