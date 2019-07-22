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

import hawkey
import os
import shutil

from dnfpluginscore import _, logger
from dnf.cli.option_parser import OptionParser
import dnf
import dnf.cli


def _pkgdir(intermediate, target):
    cwd = dnf.i18n.ucd(os.getcwd())
    return os.path.realpath(os.path.join(cwd, intermediate, target))


class RPMPayloadLocation(dnf.repo.RPMPayload):
    def __init__(self, pkg, progress, pkg_location):
        super(RPMPayloadLocation, self).__init__(pkg, progress)
        self.package_dir = os.path.dirname(pkg_location)

    def _target_params(self):
        tp = super(RPMPayloadLocation, self)._target_params()
        dnf.util.ensure_dir(self.package_dir)
        tp['dest'] = self.package_dir
        return tp


@dnf.plugin.register_command
class RepoSyncCommand(dnf.cli.Command):
    aliases = ('reposync',)
    summary = _('download all packages from remote repo')

    def __init__(self, cli):
        super(RepoSyncCommand, self).__init__(cli)

    @staticmethod
    def set_argparser(parser):
        parser.add_argument('-a', '--arch', dest='arches', default=[],
                            action=OptionParser._SplitCallback, metavar='[arch]',
                            help=_('download only packages for this ARCH'))
        parser.add_argument('--delete', default=False, action='store_true',
                            help=_('delete local packages no longer present in repository'))
        parser.add_argument('-m', '--downloadcomps', default=False, action='store_true',
                            help=_('also download comps.xml'))
        parser.add_argument('--download-metadata', default=False, action='store_true',
                            help=_('download all the metadata.'))
        parser.add_argument('-n', '--newest-only', default=False, action='store_true',
                            help=_('download only newest packages per-repo'))
        parser.add_argument('-p', '--download-path', default='./',
                            help=_('where to store downloaded repositories'))
        parser.add_argument('--metadata-path',
                            help=_('where to store downloaded repository metadata. '
                                   'Defaults to the value of --download-path.'))
        parser.add_argument('--source', default=False, action='store_true',
                            help=_('operate on source packages'))
        parser.add_argument('--remote-time', default=False, action='store_true',
                            help=_('try to set local timestamps of local files by '
                                   'the one on the server'))
        parser.add_argument('-u', '--urls', default=False, action='store_true',
                            help=_("Just list urls of what would be downloaded, "
                                   "don't download"))

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

        for repo in repos.iter_enabled():
            repo._repo.expire()
            repo.deltarpm = False

    def run(self):
        self.base.conf.keepcache = True
        for repo in self.base.repos.iter_enabled():
            if self.opts.remote_time:
                repo._repo.setPreserveRemoteTime(True)
            if self.opts.download_metadata:
                self.download_metadata(repo)
            if self.opts.downloadcomps:
                self.getcomps(repo)
            pkglist = self.get_pkglist(repo)
            if self.opts.urls:
                self.print_urls(pkglist)
            else:
                self.download_packages(pkglist)
            if self.opts.delete:
                self.delete_old_local_packages(pkglist)

    def repo_target(self, repo):
        return _pkgdir(self.opts.destdir or self.opts.download_path, repo.id)

    def metadata_target(self, repo):
        if self.opts.metadata_path:
            return _pkgdir(self.opts.metadata_path, repo.id)
        else:
            return self.repo_target(repo)

    def pkg_download_path(self, pkg):
        repo_target = self.repo_target(pkg.repo)
        pkg_download_path = os.path.realpath(
            os.path.join(repo_target, pkg.location))
        # join() ensures repo_target ends with a path separator (otherwise the
        # check would pass if pkg_download_path was a "sibling" path component
        # of repo_target that has the same prefix).
        if not pkg_download_path.startswith(os.path.join(repo_target, '')):
            raise dnf.exceptions.Error(
                _("Download target '{}' is outside of download path '{}'.").format(
                    pkg_download_path, repo_target))
        return pkg_download_path

    def delete_old_local_packages(self, packages_to_download):
        download_map = dict()
        for pkg in packages_to_download:
            download_map[(pkg.repo.id, os.path.basename(pkg.location))] = pkg.location
        # delete any *.rpm file, that is not going to be downloaded from repository
        for repo in self.base.repos.iter_enabled():
            repo_target = self.repo_target(repo)
            for dirpath, dirnames, filenames in os.walk(repo_target):
                for filename in filenames:
                    path = os.path.join(dirpath, filename)
                    if filename.endswith('.rpm') and os.path.isfile(path):
                        location = download_map.get((repo.id, filename))
                        if location is None or os.path.join(repo_target, location) != path:
                            # Delete disappeared or relocated file
                            try:
                                os.unlink(path)
                                logger.info(_("[DELETED] %s"), path)
                            except OSError:
                                logger.error(_("failed to delete file %s"), path)

    def getcomps(self, repo):
        comps_fn = repo._repo.getCompsFn()
        if comps_fn:
            dest_path = self.metadata_target(repo)
            dnf.util.ensure_dir(dest_path)
            dest = os.path.join(dest_path, 'comps.xml')
            dnf.yum.misc.decompress(comps_fn, dest=dest)
            logger.info(_("comps.xml for repository %s saved"), repo.id)

    def download_metadata(self, repo):
        repo_target = self.metadata_target(repo)
        repo._repo.downloadMetadata(repo_target)
        return True

    def get_pkglist(self, repo):
        query = self.base.sack.query(flags=hawkey.IGNORE_EXCLUDES).available().filterm(
            reponame=repo.id)
        if self.opts.newest_only:
            query = query.latest()
        if self.opts.source:
            query.filterm(arch='src')
        elif self.opts.arches:
            query.filterm(arch=self.opts.arches)
        return query

    def download_packages(self, pkglist):
        base = self.base
        progress = base.output.progress
        if progress is None:
            progress = dnf.callback.NullDownloadProgress()
        drpm = dnf.drpm.DeltaInfo(base.sack.query(flags=hawkey.IGNORE_EXCLUDES).installed(),
                                  progress, 0)
        payloads = [RPMPayloadLocation(pkg, progress, self.pkg_download_path(pkg))
                    for pkg in pkglist]
        base._download_remote_payloads(payloads, drpm, progress, None)

    def print_urls(self, pkglist):
        for pkg in pkglist:
            url = pkg.remote_location(schemes=['file', 'http', 'https', 'ftp'])
            if url:
                print(url)
            else:
                msg = _("Failed to get mirror for package: %s") % pkg.name
                logger.warning(msg)
