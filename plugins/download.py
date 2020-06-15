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
from dnf.cli.option_parser import OptionParser

import dnf
import dnf.cli
import dnf.exceptions
import dnf.i18n
import dnf.subject
import dnf.util
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
        parser.add_argument("--source", action='store_true',
                            help=_('download the src.rpm instead'))
        parser.add_argument("--debuginfo", action='store_true',
                            help=_('download the -debuginfo package instead'))
        parser.add_argument("--debugsource", action='store_true',
                            help=_('download the -debugsource package instead'))
        parser.add_argument("--arch", '--archlist', dest='arches', default=[],
                            action=OptionParser._SplitCallback, metavar='[arch]',
                            help=_("limit  the  query to packages of given architectures."))
        parser.add_argument('--resolve', action='store_true',
                            help=_('resolve and download needed dependencies'))
        parser.add_argument('--alldeps', action='store_true',
                            help=_('when running with --resolve, download all dependencies '
                                   '(do not exclude already installed ones)'))
        parser.add_argument('--url', '--urls', action='store_true', dest='url',
                            help=_('print list of urls where the rpms '
                                   'can be downloaded instead of downloading'))
        parser.add_argument('--urlprotocols', action='append',
                            choices=['http', 'https', 'rsync', 'ftp'],
                            default=[],
                            help=_('when running with --url, '
                                   'limit to specific protocols'))

    def configure(self):
        # setup sack and populate it with enabled repos
        demands = self.cli.demands
        demands.sack_activation = True
        demands.available_repos = True
        if self.opts.resolve and self.opts.alldeps:
            demands.load_system_repo = False

        if self.opts.source:
            self.base.repos.enable_source_repos()

        if self.opts.debuginfo or self.opts.debugsource:
            self.base.repos.enable_debug_repos()

        if self.opts.destdir:
            self.base.conf.destdir = self.opts.destdir
        else:
            self.base.conf.destdir = dnf.i18n.ucd(os.getcwd())

    def run(self):
        """Execute the util action here."""

        if (not self.opts.source
                and not self.opts.debuginfo
                and not self.opts.debugsource):
            pkgs = self._get_pkg_objs_rpms(self.opts.packages)
        else:
            pkgs = []
            if self.opts.source:
                pkgs.extend(self._get_pkg_objs_source(self.opts.packages))

            if self.opts.debuginfo:
                pkgs.extend(self._get_pkg_objs_debuginfo(self.opts.packages))

            if self.opts.debugsource:
                pkgs.extend(self._get_pkg_objs_debugsource(self.opts.packages))

        # If user asked for just urls then print them and we're done
        if self.opts.url:
            for pkg in pkgs:
                # command line repo packages do not have .remote_location
                if pkg.repoid != hawkey.CMDLINE_REPO_NAME:
                    url = pkg.remote_location(schemes=self.opts.urlprotocols)
                    if url:
                        print(url)
                    else:
                        msg = _("Failed to get mirror for package: %s") % pkg.name
                        if self.base.conf.strict:
                            raise dnf.exceptions.Error(msg)
                        logger.warning(msg)
            return
        else:
            self._do_downloads(pkgs)  # download rpms

    def _do_downloads(self, pkgs):
        """
        Perform the download for a list of packages
        """
        pkg_dict = {}
        for pkg in pkgs:
            pkg_dict.setdefault(str(pkg), []).append(pkg)

        to_download = []
        cmdline = []
        for pkg_list in pkg_dict.values():
            pkgs_cmdline = [pkg for pkg in pkg_list
                            if pkg.repoid == hawkey.CMDLINE_REPO_NAME]
            if pkgs_cmdline:
                cmdline.append(pkgs_cmdline[0])
                continue
            pkg_list.sort(key=lambda x: (x.repo.priority, x.repo.cost))
            to_download.append(pkg_list[0])
        if to_download:
            self.base.download_packages(to_download, self.base.output.progress)
        if cmdline:
            # command line repo packages are either local files or already downloaded urls
            # just copy them to the destination
            for pkg in cmdline:
                # python<3.4 shutil module does not raise SameFileError, check manually
                src = pkg.localPkg()
                dst = os.path.join(self.base.conf.destdir, os.path.basename(src))
                if os.path.exists(dst) and os.path.samefile(src, dst):
                    continue
                shutil.copy(src, self.base.conf.destdir)
        locations = sorted([pkg.localPkg() for pkg in to_download + cmdline])
        return locations

    def _get_pkg_objs_rpms(self, pkg_specs):
        """
        Return a list of dnf.Package objects that represent the rpms
        to download.
        """
        if self.opts.resolve:
            pkgs = self._get_packages_with_deps(pkg_specs)
        else:
            pkgs = self._get_packages(pkg_specs)
        return pkgs

    def _get_pkg_objs_source(self, pkg_specs):
        """
        Return a list of dnf.Package objects that represent the source
        rpms to download.
        """
        pkgs = self._get_pkg_objs_rpms(pkg_specs)
        source_pkgs = self._get_source_packages(pkgs)
        pkgs = set(self._get_packages(source_pkgs, source=True))
        return pkgs

    def _get_pkg_objs_debuginfo(self, pkg_specs):
        """
        Return a list of dnf.Package objects that represent the debuginfo
        rpms to download.
        """
        dbg_pkgs = set()
        q = self.base.sack.query().available()

        for pkg in self._get_packages(pkg_specs):
            for dbg_name in [pkg.debug_name, pkg.source_debug_name]:
                dbg_available = q.filter(
                    name=dbg_name,
                    epoch=int(pkg.epoch),
                    version=pkg.version,
                    release=pkg.release,
                    arch=pkg.arch
                )

                if not dbg_available:
                    continue

                for p in dbg_available:
                    dbg_pkgs.add(p)

                break

        return dbg_pkgs

    def _get_pkg_objs_debugsource(self, pkg_specs):
        """
        Return a list of dnf.Package objects that represent the debugsource
        rpms to download.
        """
        dbg_pkgs = set()
        q = self.base.sack.query().available()

        for pkg in self._get_packages(pkg_specs):
            dbg_available = q.filter(
                name=pkg.debugsource_name,
                epoch=int(pkg.epoch),
                version=pkg.version,
                release=pkg.release,
                arch=pkg.arch
            )

            for p in dbg_available:
                dbg_pkgs.add(p)

        return dbg_pkgs

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
        pkg_set = set(pkgs)
        for pkg in pkgs:
            goal = hawkey.Goal(self.base.sack)
            goal.install(pkg)
            rc = goal.run()
            if rc:
                pkg_set.update(goal.list_installs())
                pkg_set.update(goal.list_upgrades())
            else:
                msg = [_('Error in resolve of packages:')]
                logger.error("\n    ".join(msg + [str(pkg) for pkg in pkgs]))
                logger.error(dnf.util._format_resolve_problems(goal.problem_rules()))
                raise dnf.exceptions.Error()
        return pkg_set

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
        schemes = dnf.pycomp.urlparse.urlparse(pkg_spec)[0]
        is_url = schemes and schemes in ('http', 'ftp', 'file', 'https')
        if is_url or (pkg_spec.endswith('.rpm') and os.path.isfile(pkg_spec)):
            pkgs = self.base.add_remote_rpms([pkg_spec], progress=self.base.output.progress)
            return self.base.sack.query().filterm(pkg=pkgs)
        subj = dnf.subject.Subject(pkg_spec)
        q = subj.get_best_query(self.base.sack, with_src=self.opts.source)
        q = q.available()
        q = q.filterm(latest_per_arch_by_priority=True)
        if self.opts.arches:
            q = q.filter(arch=self.opts.arches)
        if len(q.run()) == 0:
            msg = _("No package %s available.") % (pkg_spec)
            raise dnf.exceptions.PackageNotFoundError(msg)
        return q

    def _get_query_source(self, pkg_spec):
        """Return a query to match a source rpm file name."""
        pkg_spec = pkg_spec[:-4]  # skip the .rpm
        subj = dnf.subject.Subject(pkg_spec)
        for nevra_obj in subj.get_nevra_possibilities():
            tmp_query = nevra_obj.to_query(self.base.sack).available()
            if tmp_query:
                return tmp_query.latest()

        msg = _("No package %s available.") % (pkg_spec)
        raise dnf.exceptions.PackageNotFoundError(msg)
