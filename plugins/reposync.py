# reposync.py
# DNF plugin adding a command to download all packages from given remote repo.
#
# Copyright (C) 2014 Red Hat, Inc.
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
from dnf.cli.option_parser import OptionParser
import dnf
import dnf.cli
import dnf.i18n
import dnf.yum.misc
import os
import sys


def _pkgdir(intermediate, target):
    cwd = dnf.i18n.ucd(os.getcwd())
    return os.path.normpath(os.path.join(cwd, intermediate, target))


@dnf.plugin.register_command
class RepoSyncCommand(dnf.cli.Command):
    aliases = ('reposync',)
    summary = _('download all packages from remote repo')

    @staticmethod
    def set_argparser(parser):
        parser.add_argument('-a', '--arch', dest='arches', default=[],
                            action=OptionParser._SplitCallback, metavar='[arch]',
                            help=_('download only packages for this ARCH'))
        parser.add_argument('--delete', default=False, action='store_true',
                            help=_('delete local packages no longer present in repository'))
        parser.add_argument('-m', '--downloadcomps', default=False, action='store_true',
                            help=_('also download comps.xml'))
        parser.add_argument('-n', '--newest-only', default=False, action='store_true',
                            help=_('download only newest packages per-repo'))
        parser.add_argument('-p', '--download-path', default='./',
                            help=_('where to store downloaded repositories '))
        parser.add_argument('--source', default=False, action='store_true',
                            help=_('operate on source packages'))

    def configure(self):
        demands = self.cli.demands
        demands.available_repos = True
        demands.sack_activation = True

        repos = self.base.repos

        if self.opts.repo:
            repos.all().disable()
            for repoid in self.opts.repo:
                try:
                    repo = repos[repoid]
                except KeyError:
                    raise dnf.cli.CliError("Unknown repo: '%s'." % repoid)
                repo.enable()

        if self.opts.source:
            repos.enable_source_repos()

        self._repo_base_path = dict()
        for repo in repos.iter_enabled():
            path = _pkgdir(self.opts.download_path, repo.id)
            self._repo_base_path[repo.id] = path
            repo.pkgdir = os.path.join(path, 'Packages')

    def delete_old_local_packages(self, packages_to_download):
        download_map = dict()
        for pkg in packages_to_download:
            download_map[(pkg.repo.id, os.path.basename(pkg.location))] = 1
        # delete any *.rpm file, that is not going to be downloaded from repository
        for repo in self.base.repos.iter_enabled():
            if os.path.exists(repo.pkgdir):
                for filename in os.listdir(repo.pkgdir):
                    path = os.path.join(repo.pkgdir, filename)
                    if filename.endswith('.rpm') and os.path.isfile(path):
                        if not (repo.id, filename) in download_map:
                            try:
                                os.unlink(path)
                                logger.info(_("[DELETED] %s"), path)
                            except OSError:
                                logger.error(_("failed to delete file %s"), path)

    def getcomps(self):
        for repo in self.base.repos.iter_enabled():
            comps_fn = repo.metadata._comps_fn
            if comps_fn:
                if not os.path.exists(repo.pkgdir):
                    try:
                        os.makedirs(repo.pkgdir)
                    except IOError:
                        logger.error(_("Could not make repository directory: %s"), repo.pkgdir)
                        sys.exit(1)
                dest = os.path.join(self._repo_base_path[repo.id], 'comps.xml')
                dnf.yum.misc.decompress(comps_fn, dest=dest)
                logger.info(_("comps.xml for repository %s saved"), repo.id)

    def run(self):
        base = self.base
        base.conf.keepcache = True

        query = base.sack.query().available()
        if self.opts.newest_only:
            query = query.latest()
        if self.opts.source:
            query = query.filter(arch='src')
        elif self.opts.arches:
            query = query.filter(arch=self.opts.arches)

        if self.opts.delete:
            self.delete_old_local_packages(query)

        if self.opts.downloadcomps:
            self.getcomps()

        base.download_packages(query, self.base.output.progress)
