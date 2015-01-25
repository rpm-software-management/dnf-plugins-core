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

import dnf
import dnf.cli
import dnfpluginscore
import os

_ = dnfpluginscore._

class RepoManage(dnf.Plugin):

    name = "repomanage"

    def __init__(self, base, cli):
        super(RepoManage, self).__init__(base, cli)
        if cli is None:
            return
        cli.register_command(RepoManageCommand)


class RepoManageCommand(dnf.cli.Command):
    aliases = ("repomanage",)
    summary = _("""
    manage a directory of rpm packages. returns lists of newest
    or oldest packages in a directory for easy piping to xargs
    or similar programs""")
    usage = "[--old] [--new] path"

    def __init__(self, args):
        super(RepoManageCommand, self).__init__(args)
        self.opts = None

    def configure(self, args):
        demands = self.cli.demands
        demands.sack_activation = True
        self.opts = self._parse_args(args)

    def run(self, *kwargs):
        if self.opts.new and self.opts.old:
            raise dnf.exceptions.Error(_("Pass either --old or --new, not both!"))

        rpm_list = []
        rpm_list = self._get_file_list(self.opts.path, ".rpm")
        verfile = {}
        pkgdict = {}

        keepnum = int(self.opts.keep)*(-1) # the number of items to keep

        if len(rpm_list) == 0:
            raise dnf.exceptions.Error(_("No files to process"))

        for pkg in rpm_list:
            try:
                self.base.add_remote_rpm(pkg)
            except IOError:
                dnfpluginscore.logger.warning(_("Could not open {}").format(pkg))

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

                if len(evrlist) < abs(keepnum):
                    newevrs = evrlist
                else:
                    newevrs = evrlist[keepnum:]

                for package in newevrs:
                    nevra = self._package_to_nevra(package)
                    for fpkg in verfile[nevra]:
                        outputpackages.append(fpkg)

        if self.opts.old:
            for (n, a) in pkgdict.keys():
                evrlist = pkgdict[(n, a)]

                if len(evrlist) < abs(keepnum):
                    continue

                oldevrs = evrlist[:keepnum]
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
    def _parse_args(args):
        alias = RepoManageCommand.aliases[0]
        parser = dnfpluginscore.ArgumentParser(alias)
        parser.add_argument("-o", "--old", action="store_true",
                            help=_("Print the older packages"))
        parser.add_argument("-n", "--new", action="store_true",
                            help=_("Print the newest packages"))
        parser.add_argument("-s", "--space", action="store_true",
                            help=_("Space separated output, not newline"))
        parser.add_argument("-k", "--keep", action="store", metavar="KEEP",
                            help=_("Newest N packages to keep - defaults to 1"),
                            default=1)
        parser.add_argument("path", action="store",
                            help=_("Path to directory"))

        return parser.parse_args(args)

    def _package_to_path(self, package):
        return os.path.join(self.opts.path, package.location)

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
    def _package_to_nevra(pkg):
        return (pkg.name, pkg.epoch, pkg.version, pkg.release, pkg.arch)
