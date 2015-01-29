# download.py, supplies the 'download' command.
#
# Copyright (C) 2013-2014  Red Hat, Inc.
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
import functools
import hawkey
import itertools
import os
import shutil


class Download(dnf.Plugin):

    name = 'download'

    def __init__(self, base, cli):
        super(Download, self).__init__(base, cli)
        self.base = base
        self.cli = cli
        if self.cli is not None:
            self.cli.register_command(DownloadCommand)


class DownloadCommand(dnf.cli.Command):

    aliases = ['download']
    summary = _('Download package to current directory')
    usage = _('PACKAGE...')

    def __init__(self, cli):
        super(DownloadCommand, self).__init__(cli)
        self.opts = None
        self.parser = None

    def configure(self, args):
        # setup sack and populate it with enabled repos
        demands = self.cli.demands
        demands.sack_activation = True
        demands.available_repos = True

    def run(self, args):
        """Execute the util action here."""

        # Setup ArgumentParser to handle util
        # You must only add options not used by dnf already
        self.parser = dnfpluginscore.ArgumentParser(self.aliases[0])
        self.parser.add_argument('packages', nargs='+',
                            help=_('packages to download'))
        self.parser.add_argument("--source", action='store_true',
                            help=_('download the src.rpm instead'))
        self.parser.add_argument('--destdir',
                            help=_('download path, default is current dir'))
        self.parser.add_argument('--resolve', action='store_true',
                            help=_('resolve and download needed dependencies'))

        # parse the options/args
        # list available options/args on errors & exit
        self.opts = self.parser.parse_args(args)

        # show util help & exit
        if self.opts.help_cmd:
            print(self.parser.format_help())
            return

        if self.opts.source:
            locations = self._download_source(self.opts.packages)
        else:
            locations = self._download_rpms(self.opts.packages)

        if self.opts.destdir:
            dest = self.opts.destdir
        else:
            dest = dnf.i18n.ucd(os.getcwd())

        move = functools.partial(self._move_package, dest)
        map(move, locations)

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
        self._enable_source_repos()
        pkgs = self._get_packages(source_pkgs, source=True)
        self.base.download_packages(pkgs, self.base.output.progress)
        locations = sorted([pkg.localPkg() for pkg in pkgs])
        return locations

    def _get_packages(self, pkg_specs, source=False):
        """Get packages matching pkg_specs."""
        if source:
            queries = map(self._get_query_source, pkg_specs)
        else:
            queries = map(self._get_query, pkg_specs)
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
            else:
                logger.info(_("No source rpm definded for %s"), str(pkg))
        return list(source_pkgs)

    def _enable_source_repos(self):
        """Enable source repositories for enabled binary repositories.

        binary repositories will be disabled and the dnf sack will be reloaded
        """
        repo_dict = {}
        # find the source repos for the enabled binary repos
        for repo in self.base.repos.iter_enabled():
            source_repo = '%s-source' % repo.id
            if source_repo in self.base.repos:
                repo_dict[repo.id] = (repo, self.base.repos[source_repo])
            else:
                repo_dict[repo.id] = (repo, None)
        # disable the binary & enable the source ones
        for id_ in repo_dict:
            repo, src_repo = repo_dict[id_]
            repo.disable()
            if src_repo:
                logger.info(_('enabled %s repository'), src_repo.id)
                src_repo.enable()
       # reload the sack
        self.base.fill_sack()

    def _get_query(self, pkg_spec):
        """Return a query to match a pkg_spec."""
        subj = dnf.subject.Subject(pkg_spec)
        q = subj.get_best_query(self.base.sack)
        q = q.available()
        q = q.latest()
        return q

    def _get_query_source(self, pkg_spec):
        """"Return a query to match a source rpm file name."""
        pkg_spec = pkg_spec[:-4]  # skip the .rpm
        nevra = hawkey.split_nevra(pkg_spec)
        q = self.base.sack.query()
        q = q.available()
        q = q.latest()
        q = q.filter(name=nevra.name, version=nevra.version,
                     release=nevra.release, arch=nevra.arch)
        return q

    @staticmethod
    def _move_package(target, location):
        """Move the downloaded package to target."""
        shutil.copy(location, target)
        os.unlink(location)
        return target
