# repomanage.py
# DNF plugin adding a command to manage rpm packages from given directory.
#
# Copyright (C) 2015 Igor Gnatenko
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
import logging
import os
import hawkey


class RepoManage(dnf.Plugin):

    name = "repomanage"

    def __init__(self, base, cli):
        super(RepoManage, self).__init__(base, cli)
        if cli is None:
            return
        cli.register_command(RepoManageCommand)


class RepoManageCommand(dnf.cli.Command):
    aliases = ("repomanage",)
    summary = _("Manage a directory of rpm packages")

    def pre_configure(self):
        if not self.opts.verbose and not self.opts.quiet:
            self.cli.redirect_logger(stdout=logging.WARNING, stderr=logging.INFO)

    def configure(self):
        if not self.opts.verbose and not self.opts.quiet:
            self.cli.redirect_repo_progress()
        demands = self.cli.demands
        demands.sack_activation = True

    def run(self):
        if self.opts.new and self.opts.old:
            raise dnf.exceptions.Error(_("Pass either --old or --new, not both!"))
        if self.opts.new and self.opts.oldonly:
            raise dnf.exceptions.Error(_("Pass either --oldonly or --new, not both!"))
        if self.opts.old and self.opts.oldonly:
            raise dnf.exceptions.Error(_("Pass either --old or --oldonly, not both!"))
        if not self.opts.old and not self.opts.oldonly:
            self.opts.new = True

        verfile = {}
        pkgdict = {}
        module_dict = {}  # {NameStream: {Version: [modules]}}
        all_modular_artifacts = set()

        keepnum = int(self.opts.keep) # the number of items to keep

        try:
            REPOMANAGE_REPOID = "repomanage_repo"
            repo_conf = self.base.repos.add_new_repo(REPOMANAGE_REPOID, self.base.conf, baseurl=[self.opts.path])
            # Always expire the repo, otherwise repomanage could use cached metadata and give identical results
            # for multiple runs even if the actual repo changed in the meantime
            repo_conf._repo.expire()
            self.base._add_repo_to_sack(repo_conf)
            if dnf.base.WITH_MODULES:
                self.base._setup_modular_excludes()

                # Prepare modules
                module_packages = self.base._moduleContainer.getModulePackages()

                for module_package in module_packages:
                    # Even though we load only REPOMANAGE_REPOID other modules can be loaded from system
                    # failsafe data automatically, we don't want them affecting repomanage results so ONLY
                    # use modules from REPOMANAGE_REPOID.
                    if module_package.getRepoID() == REPOMANAGE_REPOID:
                        all_modular_artifacts.update(module_package.getArtifacts())
                        module_dict.setdefault(module_package.getNameStream(), {}).setdefault(
                            module_package.getVersionNum(), []).append(module_package)

        except dnf.exceptions.RepoError:
            rpm_list = []
            rpm_list = self._get_file_list(self.opts.path, ".rpm")
            if len(rpm_list) == 0:
                raise dnf.exceptions.Error(_("No files to process"))

            self.base.reset(sack=True, repos=True)
            self.base.fill_sack(load_system_repo=False, load_available_repos=False)
            try:
                self.base.add_remote_rpms(rpm_list, progress=self.base.output.progress)
            except IOError:
                logger.warning(_("Could not open {}").format(', '.join(rpm_list)))

        # Prepare regular packages
        query = self.base.sack.query(flags=hawkey.IGNORE_MODULAR_EXCLUDES).available()
        packages = [x for x in query.filter(pkg__neq=query.filter(nevra_strict=all_modular_artifacts)).available()]
        packages.sort()

        for pkg in packages:
            na = (pkg.name, pkg.arch)
            if na in pkgdict:
                if pkg not in pkgdict[na]:
                    pkgdict[na].append(pkg)
            else:
                pkgdict[na] = [pkg]

            nevra = self._package_to_nevra(pkg)
            if nevra in verfile:
                verfile[nevra].append(self._package_to_path(pkg))
            else:
                verfile[nevra] = [self._package_to_path(pkg)]

        outputpackages = []
        # modular packages
        keepnum_latest_stream_artifacts = set()

        if self.opts.new:
            # regular packages
            for (n, a) in pkgdict.keys():
                evrlist = pkgdict[(n, a)]

                newevrs = evrlist[-keepnum:]

                for package in newevrs:
                    nevra = self._package_to_nevra(package)
                    for fpkg in verfile[nevra]:
                        outputpackages.append(fpkg)

            # modular packages
            for streams_by_version in module_dict.values():
                sorted_stream_versions = sorted(streams_by_version.keys())

                new_sorted_stream_versions = sorted_stream_versions[-keepnum:]

                for i in new_sorted_stream_versions:
                    for stream in streams_by_version[i]:
                        keepnum_latest_stream_artifacts.update(set(stream.getArtifacts()))

        if self.opts.old:
            # regular packages
            for (n, a) in pkgdict.keys():
                evrlist = pkgdict[(n, a)]

                oldevrs = evrlist[:-keepnum]

                for package in oldevrs:
                    nevra = self._package_to_nevra(package)
                    for fpkg in verfile[nevra]:
                        outputpackages.append(fpkg)

            # modular packages
            for streams_by_version in module_dict.values():
                sorted_stream_versions = sorted(streams_by_version.keys())

                old_sorted_stream_versions = sorted_stream_versions[:-keepnum]

                for i in old_sorted_stream_versions:
                    for stream in streams_by_version[i]:
                        keepnum_latest_stream_artifacts.update(set(stream.getArtifacts()))

        if self.opts.oldonly:
            # regular packages
            for (n, a) in pkgdict.keys():
                evrlist = pkgdict[(n, a)]

                oldevrs = evrlist[:-keepnum]

                for package in oldevrs:
                    nevra = self._package_to_nevra(package)
                    for fpkg in verfile[nevra]:
                        outputpackages.append(fpkg)

            # modular packages
            keepnum_newer_stream_artifacts = set()

            for streams_by_version in module_dict.values():
                sorted_stream_versions = sorted(streams_by_version.keys())

                new_sorted_stream_versions = sorted_stream_versions[-keepnum:]

                for i in new_sorted_stream_versions:
                    for stream in streams_by_version[i]:
                        keepnum_newer_stream_artifacts.update(set(stream.getArtifacts()))

            for streams_by_version in module_dict.values():
                sorted_stream_versions = sorted(streams_by_version.keys())

                old_sorted_stream_versions = sorted_stream_versions[:-keepnum]

                for i in old_sorted_stream_versions:
                    for stream in streams_by_version[i]:
                        for artifact in stream.getArtifacts():
                            if artifact not in keepnum_newer_stream_artifacts:
                                keepnum_latest_stream_artifacts.add(artifact)

        modular_packages = [self._package_to_path(x) for x in query.filter(pkg__eq=query.filter(nevra_strict=keepnum_latest_stream_artifacts)).available()]
        outputpackages = outputpackages + modular_packages
        outputpackages.sort()
        if self.opts.space:
            print(" ".join(outputpackages))
        else:
            for pkg in outputpackages:
                print(pkg)

    @staticmethod
    def set_argparser(parser):
        parser.add_argument("-o", "--old", action="store_true",
                            help=_("Print the older packages"))
        parser.add_argument("-O", "--oldonly", action="store_true",
                            help=_("Print the older packages. Exclude the newest packages."))
        parser.add_argument("-n", "--new", action="store_true",
                            help=_("Print the newest packages"))
        parser.add_argument("-s", "--space", action="store_true",
                            help=_("Space separated output, not newline"))
        parser.add_argument("-k", "--keep", action="store", metavar="KEEP",
                            help=_("Newest N packages to keep - defaults to 1"),
                            default=1, type=int)
        parser.add_argument("path", action="store",
                            help=_("Path to directory"))

    @staticmethod
    def _get_file_list(path, ext):
        """Return all files in path matching ext

        return list object
        """
        filelist = []
        for root, dirs, files in os.walk(path):
            for f in files:
                if os.path.splitext(f)[1].lower() == str(ext):
                    filelist.append(os.path.join(root, f))

        return filelist

    def _package_to_path(self, pkg):
        if len(self.base.repos):
            return os.path.join(self.opts.path, pkg.location)
        else:
            return pkg.location

    @staticmethod
    def _package_to_nevra(pkg):
        return (pkg.name, pkg.epoch, pkg.version, pkg.release, pkg.arch)
