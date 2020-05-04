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

        rpm_list = []
        rpm_list = self._get_file_list(self.opts.path, ".rpm")
        verfile = {}
        pkgdict = {}

        keepnum = int(self.opts.keep) # the number of items to keep

        if len(rpm_list) == 0:
            raise dnf.exceptions.Error(_("No files to process"))

        try:
            self.base.add_remote_rpms(rpm_list, progress=self.base.output.progress)
        except IOError:
            logger.warning(_("Could not open {}").format(', '.join(rpm_list)))

        packages = [x for x in self.base.sack.query().available()]
        packages.sort()
        for pkg in packages:
            na = (pkg.name, pkg.arch)
            if na in pkgdict:
                pkgdict[na].append(pkg)
            else:
                pkgdict[na] = [pkg]

            nevra = self._package_to_nevra(pkg)
            if nevra in verfile:
                verfile[nevra].append(self._package_to_path(pkg))
            else:
                verfile[nevra] = [self._package_to_path(pkg)]

        outputpackages = []

        # if new
        if not self.opts.old:
            for (n, a) in pkgdict.keys():
                evrlist = pkgdict[(n, a)]

                if len(evrlist) < keepnum:
                    newevrs = evrlist
                else:
                    newevrs = evrlist[-keepnum:]

                for package in newevrs:
                    nevra = self._package_to_nevra(package)
                    for fpkg in verfile[nevra]:
                        outputpackages.append(fpkg)

        if self.opts.old:
            for (n, a) in pkgdict.keys():
                evrlist = pkgdict[(n, a)]

                if len(evrlist) < keepnum:
                    continue

                oldevrs = evrlist[:-keepnum]
                for package in oldevrs:
                    nevra = self._package_to_nevra(package)
                    for fpkg in verfile[nevra]:
                        outputpackages.append(fpkg)

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

    @staticmethod
    def _package_to_path(pkg):
        return pkg.location

    @staticmethod
    def _package_to_nevra(pkg):
        return (pkg.name, pkg.epoch, pkg.version, pkg.release, pkg.arch)
