# repoclosure.py
# DNF plugin adding a command to display a list of unresolved dependencies
# for repositories.
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
from dnfpluginscore import _

import dnf.cli


class RepoClosure(dnf.Plugin):

    name = "repoclosure"

    def __init__(self, base, cli):
        super(RepoClosure, self).__init__(base, cli)
        if cli is None:
            return
        cli.register_command(RepoClosureCommand)


class RepoClosureCommand(dnf.cli.Command):
    aliases = ("repoclosure",)
    summary = _("Display a list of unresolved dependencies for repositories")

    def configure(self):
        demands = self.cli.demands
        demands.sack_activation = True
        demands.available_repos = True
        if self.opts.repo:
            for repo in self.base.repos.all():
                if repo.id not in self.opts.repo and repo.id not in self.opts.check:
                    repo.disable()
                else:
                    repo.enable()

    def run(self):
        if self.opts.arches:
            unresolved = self._get_unresolved(self.opts.arches)
        else:
            unresolved = self._get_unresolved()
        for pkg in sorted(unresolved.keys()):
            print("package: {} from {}".format(str(pkg), pkg.reponame))
            print("  unresolved deps:")
            for dep in unresolved[pkg]:
                print("    {}".format(dep))
        if len(unresolved) > 0:
            msg = _("Repoclosure ended with unresolved dependencies.")
            raise dnf.exceptions.Error(msg)

    def _get_unresolved(self, arch=None):
        unresolved = {}

        deps = set()
        available = self.base.sack.query().available()
        if self.base.conf.best and not self.opts.check:
            available = available.latest()
        elif self.opts.newest or self.base.conf.best:
            available = available.filter(latest_per_arch=True)
        if arch is not None:
            available = available.filter(arch=arch)
        pkgs = set()
        if self.opts.pkglist:
            available.apply()
            for pkg in self.opts.pkglist:
                for pkgs_filtered in available.filter(name=pkg):
                    pkgs.add(pkgs_filtered)
        else:
            for pkgs_filtered in available:
                pkgs.add(pkgs_filtered)

        if self.opts.check:
            checkpkgs = set()
            available.apply()
            for repo in self.opts.check:
                for pkgs_filtered in available.filter(reponame=repo):
                    checkpkgs.add(pkgs_filtered)
            pkgs.intersection_update(checkpkgs)
            # --best not applied earlier due to --check, so do it now
            if self.base.conf.best:
                available = available.latest()

        for pkg in pkgs:
            unresolved[pkg] = set()
            for req in pkg.requires:
                reqname = str(req)
                # XXX: https://bugzilla.redhat.com/show_bug.cgi?id=1186721
                if reqname.startswith("solvable:") or \
                        reqname.startswith("rpmlib("):
                    continue
                deps.add(req)
                unresolved[pkg].add(req)

        available.apply()
        unresolved_deps = set(x for x in deps if not available.filter(provides=x))

        unresolved_transition = {k: set(x for x in v if x in unresolved_deps)
                                 for k, v in unresolved.items()}
        return {k: v for k, v in unresolved_transition.items() if v}

    @staticmethod
    def set_argparser(parser):
        parser.add_argument("--arch", default=[], action="append", dest='arches',
                            help=_("check packages of the given archs, can be "
                                   "specified multiple times"))
        parser.add_argument("--check", default=[], action="append",
                            help=_("Specify repositories to check"))
        parser.add_argument("-n", "--newest", action="store_true",
                            help=_("Check only the newest packages in the "
                                   "repos"))
        parser.add_argument("--pkg", default=[], action="append",
                            help=_("Check closure for this package only"),
                            dest="pkglist")
