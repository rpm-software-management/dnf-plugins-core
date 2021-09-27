# Copyright (C) 2021  Red Hat, Inc.
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
from dnfpluginscore import _, P_, logger
from dnf.cli.option_parser import OptionParser

import os
import shutil
import subprocess

import dnf
import dnf.cli
import dnf.i18n
import hawkey


@dnf.plugin.register_command
class SyncToolCommand(dnf.cli.Command):

    aliases = ['modulesync']
    summary = _('Download packages from modules and/or create a repository with modular data')

    def __init__(self, cli):
        super(SyncToolCommand, self).__init__(cli)

    @staticmethod
    def set_argparser(parser):
        parser.add_argument('module', nargs='*', metavar=_('MODULE'),
                            help=_('modules to download'))
        parser.add_argument("--enable_source_repos", action='store_true',
                            help=_('enable repositories with source packages'))
        parser.add_argument("--enable_debug_repos", action='store_true',
                            help=_('enable repositories with debug-info and debug-source packages'))
        parser.add_argument('--resolve', action='store_true',
                            help=_('resolve and download needed dependencies'))
        parser.add_argument('-n', '--newest-only', default=False, action='store_true',
                            help=_('download only packages from newest modules'))

    def configure(self):
        # setup sack and populate it with enabled repos
        demands = self.cli.demands
        demands.sack_activation = True
        demands.available_repos = True

        demands.load_system_repo = False

        if self.opts.enable_source_repos:
            self.base.repos.enable_source_repos()

        if self.opts.enable_debug_repos:
            self.base.repos.enable_debug_repos()

        if self.opts.destdir:
            self.base.conf.destdir = self.opts.destdir
        else:
            self.base.conf.destdir = dnf.i18n.ucd(os.getcwd())

    def run(self):
        """Execute the util action here."""

        pkgs = self.base.sack.query().filterm(empty=True)
        no_matched_spec = []
        for module_spec in self.opts.module:
            try:
                pkgs = pkgs.union(self._get_packages_from_modules(module_spec))
            except dnf.exceptions.Error:
                no_matched_spec.append(module_spec)
        if no_matched_spec:
            msg = P_("Unable to find a match for argument: '{}'", "Unable to find a match for arguments: '{}'",
                     len(no_matched_spec)).format("' '".join(no_matched_spec))
            raise dnf.exceptions.Error(msg)

        if self.opts.resolve:
            pkgs = pkgs.union(self._get_providers_of_requires(pkgs))

        # download rpms
        self._do_downloads(pkgs)

        # Create a repository at destdir with modular data
        remove_tmp_moduleyamls_files = []
        for repo in self.base.repos.iter_enabled():
            module_md_path = repo.get_metadata_path('modules')
            if module_md_path:
                filename = "".join([repo.id, "-", os.path.basename(module_md_path)])
                dest_path = os.path.join(self.base.conf.destdir, filename)
                shutil.copy(module_md_path, dest_path)
                remove_tmp_moduleyamls_files.append(dest_path)
        args = ["createrepo_c", "--update", "--unique-md-filenames", self.base.conf.destdir]
        p = subprocess.run(args)
        if p.returncode:
            msg = _("Creation of repository failed with return code {}. All downloaded content was kept on the system")
            msg = msg.format(p.returncode)
            raise dnf.exceptions.Error(msg)
        for file_path in remove_tmp_moduleyamls_files:
            os.remove(file_path)

    def _do_downloads(self, pkgs):
        """
        Perform the download for a list of packages
        """
        pkg_dict = {}
        for pkg in pkgs:
            pkg_dict.setdefault(str(pkg), []).append(pkg)

        to_download = []

        for pkg_list in pkg_dict.values():
            pkg_list.sort(key=lambda x: (x.repo.priority, x.repo.cost))
            to_download.append(pkg_list[0])
        if to_download:
            self.base.download_packages(to_download, self.base.output.progress)

    def _get_packages_from_modules(self, module_spec):
        """Gets packages from modules matching module spec
        1. From module artifacts
        2. From module profiles"""
        result_query = self.base.sack.query().filterm(empty=True)
        module_base = dnf.module.module_base.ModuleBase(self.base)
        module_list, nsvcap = module_base.get_modules(module_spec)
        if self.opts.newest_only:
            module_list = self.base._moduleContainer.getLatestModules(module_list, False)
        for module in module_list:
            for artifact in module.getArtifacts():
                query = self.base.sack.query(flags=hawkey.IGNORE_EXCLUDES).filterm(nevra_strict=artifact)
                if query:
                    result_query = result_query.union(query)
                else:
                    msg = _("No match for artifact '{0}' from module '{1}'").format(
                        artifact, module.getFullIdentifier())
                    logger.warning(msg)
            if nsvcap.profile:
                profiles_set = module.getProfiles(nsvcap.profile)
            else:
                profiles_set = module.getProfiles()
            if profiles_set:
                for profile in profiles_set:
                    for pkg_name in profile.getContent():
                        query = self.base.sack.query(flags=hawkey.IGNORE_EXCLUDES).filterm(name=pkg_name)
                        # Prefer to add modular providers selected by argument
                        if result_query.intersection(query):
                            continue
                        # Add all packages with the same name as profile described
                        elif query:
                            result_query = result_query.union(query)
                        else:
                            msg = _("No match for package name '{0}' in profile {1} from module {2}")\
                                .format(pkg_name, profile.getName(), module.getFullIdentifier())
                            logger.warning(msg)
        if not module_list:
            msg = _("No mach for argument '{}'").format(module_spec)
            raise dnf.exceptions.Error(msg)

        return result_query

    def _get_providers_of_requires(self, to_test, done=None, req_dict=None):
        done = done if done else to_test
        # req_dict = {}  {req : set(pkgs)}
        if req_dict is None:
            req_dict = {}
        test_requires = []
        for pkg in to_test:
            for require in pkg.requires:
                if require not in req_dict:
                    test_requires.append(require)
                req_dict.setdefault(require, set()).add(pkg)

        if self.opts.newest_only:
            #  Prepare cache with all packages related affected by modular filtering
            names = set()
            for module in self.base._moduleContainer.getModulePackages():
                for artifact in module.getArtifacts():
                    name, __, __ = artifact.rsplit("-", 2)
                    names.add(name)
            modular_related = self.base.sack.query(flags=hawkey.IGNORE_EXCLUDES).filterm(provides=names)

        requires = self.base.sack.query().filterm(empty=True)
        for require in test_requires:
            q = self.base.sack.query(flags=hawkey.IGNORE_EXCLUDES).filterm(provides=require)

            if not q:
                #  TODO(jmracek) Shell we end with an error or with RC 1?
                logger.warning((_("Unable to satisfy require {}").format(require)))
            else:
                if self.opts.newest_only:
                    if not modular_related.intersection(q):
                        q.filterm(latest_per_arch_by_priority=1)
                requires = requires.union(q.difference(done))
        done = done.union(requires)
        if requires:
            done = self._get_providers_of_requires(requires, done=done, req_dict=req_dict)

        return done
